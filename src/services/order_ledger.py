"""Persistent order-intent ledger and broker reconciliation.

Before this, the watcher's only memory of an order it had placed was
``_placed_orders`` — an in-process dict with a five-minute TTL. A pod
restart, a rollout, or a node reboot erased it, and the code said so:
"a restart reopens the gap for one cycle (acceptable)". Combined with a
transport timeout, whose response tells you nothing about whether the broker
booked the order, that is a duplicate-order machine (P0-2 of
``docs/ops/system-evaluation-2026-07-26.md``).

This module gives every order a durable row that is written **before** the
request goes out and updated with whatever we learn afterwards, so the
answer to "did we already order this?" survives the process.

## State machine

``INTENDED``
    Committed to disk immediately before the API call. If the process dies
    here, restart finds a row with no order number and must reconcile it
    against the broker rather than assume nothing happened.
``SUBMITTED``
    The broker accepted the request (``order_result.submitted``).
``UNKNOWN``
    The request went out and the answer was lost — read timeout, connection
    reset, 5xx. **A buy is never resubmitted off this state.** A protective
    sell is also held initially, but may move to the explicitly local
    ``RELEASED`` state under the bounded absence policy below.
``OPEN`` / ``PARTIAL``
    Reconciliation found the order live at the broker, with nothing or
    something filled so far.
``RELEASED``
    Terminal *local-policy* state, not a broker verdict. It applies only to a
    protective ``UNKNOWN`` sell after a 120-second grace and three complete
    ka10075+ka10076 views, at least 30 seconds apart, all show no plausible
    broker row. It releases only the sell-quantity lock so a later stop-loss
    can retry; it never applies to buys.
``FILLED`` / ``CANCELLED`` / ``REJECTED``
    Terminal. A rejected order releases its slot — a rejection is proof the
    broker holds nothing, so retrying is safe.

``INTENDED``, ``SUBMITTED``, ``UNKNOWN``, ``OPEN`` and ``PARTIAL`` are all
"unresolved": we may have live exposure we cannot see, so they gate new
orders.

## Exactly-once is impossible here — what we do instead

Kiwoom's order APIs (kt10000/kt10001/kt10002/kt10003) accept **no client
order id**, and their documented response bodies do not even return
``ord_no`` (see ``order_result.extract_order_no``). Without an
idempotency key that the broker echoes back there is no way to ask "did my
order #X land?" — only "is there *an* order that looks like mine?".

So this ledger implements conservative dedup, not exactly-once:

* A **decision key** is derived deterministically from ``(trading_day,
  stock_code, side, quantity, price, instruction scope, time bucket)``, and an
  **attempt id** identifies one try at that decision. Splitting them is what
  makes a replay safe: :meth:`OrderLedger.record_intent` tells the caller
  whether it created a fresh attempt (submit allowed), found one already in
  flight (do not submit), found the decision already ``FILLED``/``CANCELLED``
  (refuse, and leave the audit row untouched), or is retrying after a
  ``REJECTED`` (new attempt row, prior rejection preserved). Returning the
  found row and calling it new is what let a same-bucket replay send a second
  order and then overwrite the row that proved the first one.
* Registration is **atomic and cross-process safe**. The read and the insert
  run inside one ``BEGIN IMMEDIATE``, and a primary-key collision from a
  racing connection is re-read and reported as an ordinary duplicate rather
  than a storage fault — the distinction matters because the protective-order
  path treats a fault as "proceed anyway", so mislabelling a race would turn
  it into a real double sell.
* Rows written **before decision scopes existed** are bridged into the current
  lineage by canonical tuple ``(day, code, side, qty, price, bucket)`` rather
  than by key. Their old hash has no scope component and so can never be
  recomputed, and rewriting it is out of the question because a settled row is
  the audit record. Legacy rows keep their original ``decision_key`` and are
  recognised by ``decision_scope IS NULL``; a lineage may therefore span two
  key values, which :meth:`OrderLedger.decision_history` shows. Because only
  scope-less rows bridge, new instructions of the same size (``TRIM 5`` vs
  ``CUT_LOSS 5``) stay separate decisions.
* An order with a broker number reconciles exactly, by number.
* An order *without* one (crashed before submit, or a lost response) is
  matched only when **all** of the following hold: same code, side and
  ordered quantity; compatible price; a *readable timestamp* on the same
  trading day that is not clearly earlier than the moment the intent was
  written; the row's order number not already owned by any other ledger row,
  terminal ones included; and exactly one candidate qualifies.
* **When a match cannot be made — or when two could — the intent stays
  unresolved and keeps blocking.** That is the deliberate failure mode: a
  blocked entry costs an opportunity, a duplicated one costs money.
* The one deliberately asymmetric liveness escape is an ``UNKNOWN``
  protective sell. Kiwoom documents neither an absence guarantee nor an
  eventual-consistency SLA for ka10075/ka10076, so an empty response is not
  called ``REJECTED`` or ``CANCELLED``. Instead, after the approved grace and
  repeated complete observations it becomes ``RELEASED`` with an append-only
  audit trail. Any incomplete query or plausible broker row resets the
  absence streak. This bounds both failure modes: one delayed snapshot cannot
  cause a duplicate sell, and one lost response cannot trap the position
  forever.

Identity alone is deliberately *not* sufficient, and the timestamp and
ownership rules are not belt-and-braces. Two concrete ways the earlier
identity-only matcher went wrong:

* A 09:00 fill and a 14:00 lost-response intent for the same stock and size
  are indistinguishable by identity. Adopting the morning fill marked the
  afternoon intent ``FILLED`` off somebody else's trade and released the
  duplicate-order block — the exact outcome the ledger exists to prevent.
* Claimed order numbers were collected from *currently unresolved* rows only,
  so a number already attributed to a settled ``FILLED`` row was fair game
  and could be stolen by a later intent, which then inherited its fill.

Order-number identity is therefore the composite ``(trading_day,
normalized order_no)`` — never the number alone. Kiwoom order numbers are 7
digits and the spec guarantees no uniqueness beyond a session, so they read as
a daily sequence. Owning them globally would be safe but would *decay*: every
terminal row the ledger had ever written would forbid that number forever, and
as the file grew an increasing share of legitimate same-number orders would
become unmatchable until reconciliation stopped resolving anything. Scoping to
the day keeps both properties — a settled row still owns its number for its own
session (so the stale-fill defence above holds), and tomorrow's recycled number
is free.

Known residual risks, none of them fixable from this side:

1. Two genuinely distinct orders with the same code, side, quantity, price
   *and* instruction inside one 60-second bucket collapse into one decision.
   The scope component keeps different instructions apart (``TRIM 5`` vs
   ``CUT_LOSS 5``), and the next bucket or any different size is a new
   decision, so this cannot trap a position — but a true same-instruction
   double inside one minute is refused by design.
2. If the broker books an order and it never appears in either the
   open-order or execution query, nothing can resolve it.
3. ``kiwoom_api_spec.md`` does not document the encoding of ``tm``/``ord_tm``.
   Unrecognized encodings parse as "no time", which blocks rather than
   guesses — so the failure is a stuck intent and a refused entry, never a
   duplicate order. See :func:`parse_broker_time`.
4. The broker does not promise how quickly a newly accepted order appears in
   ka10075/ka10076. ``RELEASED`` therefore reduces, but cannot eliminate, the
   chance that an order hidden for longer than the policy window later
   appears. Every retry still refreshes both broker views first and sizes from
   holdings minus visible/ledger working sells; Kiwoom may reject an excess
   sell, but exactly-once remains impossible without a client order id.
4. A time-of-day-only stamp is dated to the query's own trading day. Both
   broker queries are same-day queries, so this holds; a future caller that
   asks for historical rows would have to supply the date instead.

An empty ledger is separately not evidence that the broker is idle — it says
only that *we* have no record, which is exactly what a fresh install, a wiped
volume, an older build, or a hand-placed order leaves behind. So the buy path
also inspects the live open-order view directly (:func:`open_buy_quantity`)
and refuses to open exposure while the broker still has a working buy for
that stock. Such orders are **blocked on, never adopted** into the ledger: we
did not place them and do not know their lifecycle, so inventing an intent
for one would make our own bookkeeping lie. Blocking is sufficient and cannot
mis-attribute anything.

## Failure policy

The ledger is a safety device, so its own failure is not allowed to be
silent — but the right response depends on the direction of the trade:

* **Buys fail closed.** No ledger, no new exposure.
* **Protective sells and cancels proceed**, with an alert. A ledger fault
  must never trap the account in a position; an un-recorded exit is a
  bookkeeping problem, a blocked exit is an unbounded loss. Callers are
  expected to page a human.

The on-disk ledger additionally requires a local block filesystem (or a
client/server database implemented outside this module). SQLite WAL with
``synchronous=FULL`` does not make NFS/CIFS/SMB/SSHFS locking and durability
semantics safe. Before opening the database, Linux mount metadata is parsed
and the longest matching mount point is classified. A confirmed network
filesystem refuses to open the ledger, which invokes the asymmetric policy
above. Missing, unreadable, or unrecognised metadata is reported as
``unknown`` but does not block local development; production must make the
filesystem assumption independently verifiable. Journal mode is never
downgraded as a purported fix.

Oversell protection is separate and always applies: a sell is capped by
holdings minus quantity already working at the broker, so a stop-loss
re-firing while an earlier sell is still open cannot sell the same shares
twice. The watcher refreshes the broker's open orders immediately before it
sizes an exit, independently of any polling or stale-cancel configuration.

**Residual risk when that refresh fails.** The exit still goes out — a
blocked exit is the worse outcome — sized against the cached broker view plus
this ledger's own unresolved sell intents, with an alert. In that window a
sell order placed outside this watcher, or after the cache was last good, is
invisible, so the request can exceed the holding. The consequence is a broker
rejection rather than a real oversell: Kiwoom will not fill beyond the
position. It is recorded as a normal ``REJECTED`` intent and can be retried.
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Iterable
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")

log = logging.getLogger("kiwoom.watcher.order_ledger")

DEFAULT_LEDGER_PATH = (
    Path(__file__).resolve().parents[2] / "output" / "order_ledger.sqlite3"
)
LINUX_MOUNTINFO_PATH = Path("/proc/self/mountinfo")

STORAGE_LOCAL = "local"
STORAGE_NETWORK = "network"
STORAGE_UNKNOWN = "unknown"

# Exact filesystem names reported by Linux mountinfo. Do not classify every
# FUSE filesystem as remote: several are local, and metadata uncertainty is
# explicitly non-blocking. The remote implementations we know are listed
# instead.
NETWORK_FILESYSTEM_TYPES = frozenset(
    {
        "9p",
        "afs",
        "ceph",
        "cifs",
        "coda",
        "davfs",
        "fuse.ceph",
        "fuse.glusterfs",
        "fuse.rclone",
        "fuse.smbnetfs",
        "fuse.sshfs",
        "gcsfuse",
        "glusterfs",
        "lustre",
        "ncpfs",
        "nfs",
        "nfs4",
        "smb3",
        "smbfs",
        "sshfs",
    }
)
LOCAL_FILESYSTEM_TYPES = frozenset(
    {
        "apfs",
        "btrfs",
        "ext2",
        "ext3",
        "ext4",
        "jfs",
        "overlay",
        "ramfs",
        "reiserfs",
        "tmpfs",
        "ubifs",
        "ufs",
        "xfs",
        "zfs",
    }
)

# -- states -----------------------------------------------------------------

STATE_INTENDED = "INTENDED"
STATE_SUBMITTED = "SUBMITTED"
STATE_UNKNOWN = "UNKNOWN"
STATE_OPEN = "OPEN"
STATE_PARTIAL = "PARTIAL"
STATE_FILLED = "FILLED"
STATE_CANCELLED = "CANCELLED"
STATE_REJECTED = "REJECTED"
STATE_RELEASED = "RELEASED"

ALL_STATES = frozenset(
    {
        STATE_INTENDED,
        STATE_SUBMITTED,
        STATE_UNKNOWN,
        STATE_OPEN,
        STATE_PARTIAL,
        STATE_FILLED,
        STATE_CANCELLED,
        STATE_REJECTED,
        STATE_RELEASED,
    }
)

# States where the broker may be holding something for us.
UNRESOLVED_STATES = frozenset(
    {STATE_INTENDED, STATE_SUBMITTED, STATE_UNKNOWN, STATE_OPEN, STATE_PARTIAL}
)
TERMINAL_STATES = frozenset(
    {STATE_FILLED, STATE_CANCELLED, STATE_REJECTED, STATE_RELEASED}
)

SIDE_BUY = "buy"
SIDE_SELL = "sell"
SIDE_CANCEL = "cancel"

# Two identical decisions inside this window are treated as one intent. Small
# enough that a genuine re-entry later in the session gets its own row.
DEFAULT_BUCKET_SECONDS = 60

# Local liveness policy for a protective sell whose submit response was lost.
# These are safety constants, not strategy thresholds. They are intentionally
# not configurable from deployment flags: changing them requires a code review
# because a shorter window trades duplicate-sell risk for faster recovery.
UNKNOWN_SELL_RELEASE_GRACE_SECONDS = 120
UNKNOWN_SELL_RELEASE_MIN_OBSERVATIONS = 3
UNKNOWN_SELL_RELEASE_MIN_INTERVAL_SECONDS = 30

# How long a connection waits for another writer's lock before giving up. A
# registration critical section is a few microseconds of work, so anything
# beyond this is a stuck process rather than contention.
_BUSY_TIMEOUT_SECONDS = 10.0


class OrderLedgerError(RuntimeError):
    """The ledger could not be read or written.

    Callers must translate this into their side's policy: fail closed for
    buys, proceed-with-alert for protective sells and cancels.
    """


@dataclass(frozen=True, slots=True)
class MountInfoEntry:
    """The mount fields needed for ledger storage classification."""

    mount_point: Path
    fs_type: str
    source: str


@dataclass(frozen=True, slots=True)
class LedgerStorageSafety:
    """Auditable result of classifying the ledger's backing filesystem."""

    state: str
    reason: str
    ledger_path: str | None
    mount_point: str | None = None
    fs_type: str | None = None
    source: str | None = None
    metadata_available: bool = True

    @property
    def blocks_new_entries(self) -> bool:
        return self.state == STORAGE_NETWORK

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state,
            "blocks_new_entries": self.blocks_new_entries,
            "reason": self.reason,
            "ledger_path": self.ledger_path,
            "mount_point": self.mount_point,
            "fs_type": self.fs_type,
            "source": self.source,
            "metadata_available": self.metadata_available,
        }


class UnsafeLedgerStorageError(OrderLedgerError):
    """The ledger path is confirmed to be on an unsafe network filesystem."""

    def __init__(self, safety: LedgerStorageSafety):
        self.safety = safety
        super().__init__(safety.reason)


# -- helpers ----------------------------------------------------------------


_MOUNT_ESCAPE_RE = re.compile(r"\\([0-7]{3})")


def _decode_mount_field(value: str) -> str:
    """Decode the octal escapes used by ``/proc/*/mountinfo`` fields."""

    return _MOUNT_ESCAPE_RE.sub(lambda match: chr(int(match.group(1), 8)), value)


def parse_linux_mountinfo(text: str) -> list[MountInfoEntry]:
    """Parse Linux mountinfo text without reading the filesystem.

    Malformed rows are ignored. The caller can distinguish an empty/invalid
    document from a usable one and treat it as unknown rather than guessing.
    """

    mounts: list[MountInfoEntry] = []
    for raw_line in text.splitlines():
        before, separator, after = raw_line.partition(" - ")
        if not separator:
            continue
        left_fields = before.split()
        right_fields = after.split()
        if len(left_fields) < 5 or len(right_fields) < 2:
            continue
        mount_point = Path(_decode_mount_field(left_fields[4]))
        if not mount_point.is_absolute():
            continue
        mounts.append(
            MountInfoEntry(
                mount_point=mount_point,
                fs_type=right_fields[0].strip().lower(),
                source=_decode_mount_field(right_fields[1]),
            )
        )
    return mounts


def _absolute_lexical_path(path: Path | str) -> Path:
    """Absolute, normalised path without resolving symlinks or requiring I/O."""

    return Path(os.path.abspath(os.fspath(path)))


def classify_ledger_storage(
    path: Path | str,
    mountinfo_text: str,
) -> LedgerStorageSafety:
    """Classify ``path`` from injected mountinfo using longest-prefix match."""

    ledger_path = _absolute_lexical_path(path)
    mounts = parse_linux_mountinfo(mountinfo_text)
    matches: list[MountInfoEntry] = []
    for mount in mounts:
        mount_point = _absolute_lexical_path(mount.mount_point)
        if ledger_path == mount_point or mount_point in ledger_path.parents:
            matches.append(
                MountInfoEntry(
                    mount_point=mount_point,
                    fs_type=mount.fs_type,
                    source=mount.source,
                )
            )
    if not matches:
        return LedgerStorageSafety(
            state=STORAGE_UNKNOWN,
            reason=(
                f"no mount metadata entry covers ledger path {ledger_path}; "
                "storage safety unknown (not blocked)"
            ),
            ledger_path=str(ledger_path),
            metadata_available=bool(mounts),
        )

    mount = max(matches, key=lambda item: len(item.mount_point.parts))
    fields = {
        "ledger_path": str(ledger_path),
        "mount_point": str(mount.mount_point),
        "fs_type": mount.fs_type,
        "source": mount.source,
        "metadata_available": True,
    }
    if mount.fs_type in NETWORK_FILESYSTEM_TYPES:
        return LedgerStorageSafety(
            state=STORAGE_NETWORK,
            reason=(
                f"unsafe order ledger storage: {ledger_path} is on confirmed "
                f"network filesystem {mount.fs_type} mounted at "
                f"{mount.mount_point} (source {mount.source}); SQLite "
                "WAL+synchronous=FULL is not a safe substitute for local "
                "block storage. Move the ledger to a local block filesystem "
                "or a client/server database, then restart; new buys remain "
                "blocked while protective sells and cancels stay allowed."
            ),
            **fields,
        )
    if mount.fs_type in LOCAL_FILESYSTEM_TYPES:
        return LedgerStorageSafety(
            state=STORAGE_LOCAL,
            reason=(
                f"ledger path {ledger_path} is on local filesystem "
                f"{mount.fs_type} mounted at {mount.mount_point}"
            ),
            **fields,
        )
    return LedgerStorageSafety(
        state=STORAGE_UNKNOWN,
        reason=(
            f"ledger path {ledger_path} matched unclassified filesystem "
            f"{mount.fs_type} at {mount.mount_point}; storage safety unknown "
            "(not blocked)"
        ),
        **fields,
    )


def read_linux_mountinfo() -> str:
    """Read the current Linux process mount table (inject in tests)."""

    return LINUX_MOUNTINFO_PATH.read_text(encoding="utf-8")


def inspect_ledger_storage(
    path: Path | str,
    *,
    mountinfo_reader: Callable[[], str] | None = None,
) -> LedgerStorageSafety:
    """Read and classify mount metadata, keeping missing metadata non-blocking."""

    reader = mountinfo_reader or read_linux_mountinfo
    ledger_path = str(_absolute_lexical_path(path))
    try:
        mountinfo_text = reader()
    except OSError as exc:
        return LedgerStorageSafety(
            state=STORAGE_UNKNOWN,
            reason=(
                f"mount metadata unavailable for ledger path {ledger_path}: "
                f"{type(exc).__name__}: {exc}; storage safety unknown "
                "(not blocked)"
            ),
            ledger_path=ledger_path,
            metadata_available=False,
        )
    return classify_ledger_storage(path, mountinfo_text)


def _now(now: datetime | None = None) -> datetime:
    current = now or datetime.now(KST)
    if current.tzinfo is None:
        current = current.replace(tzinfo=KST)
    return current.astimezone(KST)


def _to_int(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    text = str(value).strip().replace(",", "").replace("+", "")
    if not text or text == "-":
        return None
    try:
        return int(float(text))
    except (TypeError, ValueError):
        return None


def normalize_order_no(value: Any) -> str | None:
    """Comparable broker order number (leading zeroes dropped, ``0`` → None)."""

    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return text.lstrip("0") or None
    return text


def make_decision_key(
    *,
    trading_day: str,
    stock_code: str,
    side: str,
    quantity: int,
    price: int | None,
    scope: str | None = None,
    now: datetime | None = None,
    bucket_seconds: int = DEFAULT_BUCKET_SECONDS,
) -> str:
    """Deterministic key for one trading **decision**.

    Same decision, same bucket, same key — so a replay finds the existing
    decision instead of silently opening a second one. This is *not* an
    attempt id: one decision can legitimately have several attempts (a
    rejection may be retried), and conflating the two is what let a replay
    overwrite a settled row. See :func:`make_attempt_id` and
    :meth:`OrderLedger.record_intent`.

    ``scope`` names the *instruction* behind the decision — the ACTION tag for
    an agent order, the trigger type for a Tier-1 rule. Without it, two
    genuinely different instructions that coincide in size collapse into one
    decision: ``TRIM 5`` followed by ``CUT_LOSS 5`` on a 10-share position is
    a legitimate full exit, and treating the second as a replay of the first
    would refuse it. Size alone is not an instruction.
    """

    stamp = _now(now)
    bucket = decision_bucket_for(stamp, bucket_seconds)
    raw = (
        f"{trading_day}|{stock_code}|{side}|{quantity}"
        f"|{price if price is not None else '-'}"
        f"|{scope or '-'}|{bucket}"
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


def decision_bucket_for(
    stamp: datetime, bucket_seconds: int = DEFAULT_BUCKET_SECONDS
) -> int:
    """The dedup time bucket a moment falls into.

    Shared by :func:`make_decision_key` and the legacy backfill so both agree
    on what "same bucket" means.
    """

    return int(_now(stamp).timestamp()) // max(bucket_seconds, 1)


def make_attempt_id(decision_key: str, attempt: int) -> str:
    """Primary key for one attempt at ``decision_key``.

    Attempt 1 keeps the bare decision key so rows written before attempts
    existed remain addressable by their original id — the migration in
    :meth:`OrderLedger._migrate` relies on it.
    """

    return decision_key if attempt <= 1 else f"{decision_key}#{attempt}"


def parse_broker_time(
    row: dict[str, Any], *, reference_day: date
) -> tuple[datetime | None, date | None]:
    """Normalize a broker row's timestamp to KST. ``(at, trading_day)``.

    Returns ``(None, None)`` when the row carries no readable time — and that
    is a load-bearing outcome, not a shrug: a row whose time we cannot read
    can never be matched to an unnumbered intent, so an unreadable format
    over-blocks (a missed entry) instead of under-blocking (a duplicate
    order).

    Fields, in descending authority:

    * ``ord_tmd`` — 14 digits ``YYYYMMDDHHMMSS``. Carries its own date, so it
      is the only field that can *disprove* a same-day assumption.
    * ``ord_tm`` (ka10076 주문시간) / ``tm`` (ka10075 시간) — time of day only,
      so the date comes from ``reference_day``. Sound because both queries are
      same-day queries: ka10075 returns today's working orders and ka10076 is
      called with ``qry_tp=0`` for today's fills.

    ``kiwoom_api_spec.md`` documents **no format** for ``tm``/``ord_tm``
    (String, length 20, no note); only date fields are specified as
    ``YYYYMMDD``. The encodings accepted here follow the convention already
    in production in ``watcher_triggers.detect_tier1_stale_orders`` plus the
    obvious punctuated variants. Anything else parses as ``None``.
    """

    raw_full = str(row.get("ord_tmd") or "").strip()
    if len(raw_full) == 14 and raw_full.isdigit():
        try:
            stamp = datetime.strptime(raw_full, "%Y%m%d%H%M%S").replace(tzinfo=KST)
        except ValueError:
            pass
        else:
            return stamp, stamp.date()

    for key in ("ord_tm", "tm", "cntr_tm"):
        raw = str(row.get(key) or "").strip()
        if not raw:
            continue
        digits = raw.replace(":", "").replace(" ", "")
        if not digits.isdigit():
            continue
        if len(digits) == 14:
            try:
                stamp = datetime.strptime(digits, "%Y%m%d%H%M%S").replace(tzinfo=KST)
            except ValueError:
                continue
            return stamp, stamp.date()
        if len(digits) in (4, 6):
            fmt = "%H%M" if len(digits) == 4 else "%H%M%S"
            try:
                clock = datetime.strptime(digits, fmt).time()
            except ValueError:
                continue
            stamp = datetime.combine(reference_day, clock, tzinfo=KST)
            return stamp, reference_day
    return None, None


def row_side(row: dict[str, Any]) -> str | None:
    """Best-effort buy/sell classification of a broker order row.

    ``io_tp_nm`` (주문구분) is free text — "매수", "+매수", "현금매도" — so it is
    matched by substring rather than equality.
    """

    text = str(row.get("io_tp_nm") or row.get("trde_tp") or "")
    if "매수" in text:
        return SIDE_BUY
    if "매도" in text:
        return SIDE_SELL
    return None


def normalize_stock_code(value: Any) -> str:
    """Comparable stock code across Kiwoom responses.

    Account holdings come back as ``A105560`` while leaderboards, the roster,
    open orders and executions all use the bare six digits, so any comparison
    that mixes the two must go through here. Public because the buy-path
    gates in `strategy`/`watcher` need exactly this rule — a second copy is
    how the two drift apart.
    """

    return str(value or "").strip().upper().lstrip("A")


# Internal alias kept so the reconciliation call sites read unchanged.
_normalize_code = normalize_stock_code


def _remaining_quantity(row: dict[str, Any]) -> int:
    """Shares of one broker row still working."""

    remaining = _to_int(row.get("oso_qty"))
    if remaining is None:
        # No remaining-quantity field: assume the whole order is working
        # rather than assume zero.
        remaining = _to_int(row.get("ord_qty")) or 0
    return max(remaining, 0)


def _open_quantity(
    open_orders: Iterable[Any],
    stock_code: str,
    side: str,
    *,
    include_unclassified: bool = False,
) -> int:
    code = _normalize_code(stock_code)
    total = 0
    for row in open_orders or []:
        if not isinstance(row, dict):
            continue
        if _normalize_code(row.get("stk_cd")) != code:
            continue
        this_side = row_side(row)
        if this_side != side and not (include_unclassified and this_side is None):
            continue
        total += _remaining_quantity(row)
    return total


def open_sell_quantity(open_orders: Iterable[Any], stock_code: str) -> int:
    """Shares of ``stock_code`` already working as sell orders at the broker.

    This is the oversell guard's other half: whatever is here is spoken for
    and must not be sold again by a re-firing stop-loss.
    """

    return _open_quantity(open_orders, stock_code, SIDE_SELL)


def open_buy_quantity(
    open_orders: Iterable[Any],
    stock_code: str,
    *,
    include_unclassified: bool = False,
) -> int:
    """Shares of ``stock_code`` already working as buy orders at the broker.

    Unlike the sell side, this is not about our own bookkeeping: it catches
    orders **this ledger has never heard of** — placed by hand, by an older
    build, or by another process — which no local intent can represent. A
    clean ledger says nothing about those, so the buy path has to look.

    ``include_unclassified`` also counts rows for this stock whose side we
    could not read (no ``io_tp_nm``/``trde_tp``). The buy gate turns that on:
    an unreadable row with quantity still working might be a buy, and a
    blocked entry costs an opportunity while a duplicated one costs money.
    """

    return _open_quantity(
        open_orders,
        stock_code,
        SIDE_BUY,
        include_unclassified=include_unclassified,
    )


# -- rows -------------------------------------------------------------------


# What `record_intent` did. The caller must branch on this: only `created`
# authorizes an order API call.
REGISTRATION_CREATED = "created"
REGISTRATION_EXISTING_OPEN = "existing_open"
REGISTRATION_TERMINAL = "terminal"


@dataclass(slots=True)
class OrderIntent:
    """One **attempt** at a decision, and everything we know about its fate.

    ``decision_key`` identifies the trading decision (day, stock, side,
    quantity, price, time bucket). ``intent_id`` identifies this attempt at
    it. They are deliberately distinct — see :meth:`OrderLedger.record_intent`.
    """

    intent_id: str
    trading_day: str
    stock_code: str
    side: str
    quantity: int
    price: int | None
    state: str
    order_no: str | None = None
    filled_quantity: int = 0
    reason: str | None = None
    origin: str | None = None
    created_at: str = ""
    updated_at: str = ""
    decision_key: str = ""
    attempt: int = 1
    # ``None`` scope means this row predates scoped decision keys; see
    # ``OrderLedger._legacy_bridge_rows``.
    decision_scope: str | None = None
    decision_bucket: int | None = None
    unknown_since: str | None = None
    absence_observation_count: int = 0
    absence_first_observed_at: str | None = None
    absence_last_observed_at: str | None = None
    released_at: str | None = None

    @property
    def is_legacy(self) -> bool:
        """True for a row written before decision scopes existed."""

        return self.decision_scope is None

    @property
    def unresolved(self) -> bool:
        return self.state in UNRESOLVED_STATES

    @property
    def remaining_quantity(self) -> int:
        return max(self.quantity - self.filled_quantity, 0)

    @property
    def notional(self) -> int:
        """Value still committed by this intent, for exposure gating."""

        return self.remaining_quantity * (self.price or 0)

    def to_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "trading_day": self.trading_day,
            "stock_code": self.stock_code,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "state": self.state,
            "order_no": self.order_no,
            "filled_quantity": self.filled_quantity,
            "reason": self.reason,
            "origin": self.origin,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "decision_key": self.decision_key,
            "attempt": self.attempt,
            "decision_scope": self.decision_scope,
            "decision_bucket": self.decision_bucket,
            "unknown_since": self.unknown_since,
            "absence_observation_count": self.absence_observation_count,
            "absence_first_observed_at": self.absence_first_observed_at,
            "absence_last_observed_at": self.absence_last_observed_at,
            "released_at": self.released_at,
        }


@dataclass(slots=True)
class ReconcileReport:
    """What one reconciliation pass resolved, and what it could not."""

    checked: int = 0
    resolved: int = 0
    still_unresolved: int = 0
    adopted_order_no: int = 0
    released: int = 0
    absence_observed: int = 0
    absence_resets: int = 0
    unmatched: list[str] = None  # type: ignore[assignment]
    # Intents with two or more plausible broker candidates. Left unresolved on
    # purpose — they keep blocking new buys until a human or a later, clearer
    # broker view settles them.
    ambiguous: list[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.unmatched is None:
            self.unmatched = []
        if self.ambiguous is None:
            self.ambiguous = []

    def to_dict(self) -> dict[str, Any]:
        return {
            "checked": self.checked,
            "resolved": self.resolved,
            "still_unresolved": self.still_unresolved,
            "adopted_order_no": self.adopted_order_no,
            "released": self.released,
            "absence_observed": self.absence_observed,
            "absence_resets": self.absence_resets,
            "unmatched": list(self.unmatched),
            "ambiguous": list(self.ambiguous),
        }


@dataclass(slots=True)
class IntentRegistration:
    """Outcome of asking the ledger to record a decision.

    The caller **must** branch on :attr:`may_submit`. Before this existed,
    ``record_intent`` returned whatever row it found for the decision key and
    the caller could not tell a fresh insert from a replay — so a same-bucket
    replay of an already-``FILLED`` decision handed back the settled row, the
    watcher sent a *second* order, and settling that order overwrote the
    original row's state. One duplicate trade, one destroyed audit record.
    """

    outcome: str
    intent: OrderIntent | None = None
    reason: str | None = None

    @property
    def may_submit(self) -> bool:
        """True only for a row this call newly inserted."""

        return self.outcome == REGISTRATION_CREATED

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome": self.outcome,
            "reason": self.reason,
            "intent": self.intent.to_dict() if self.intent else None,
        }


_SCHEMA = """
CREATE TABLE IF NOT EXISTS order_intents (
    intent_id       TEXT PRIMARY KEY,
    decision_key    TEXT,
    attempt         INTEGER NOT NULL DEFAULT 1,
    -- NULL scope marks a pre-scope (legacy) row; new rows always write a
    -- string, '' when the caller supplied none. See `_legacy_bridge_rows`.
    decision_scope  TEXT,
    decision_bucket INTEGER,
    trading_day     TEXT NOT NULL,
    stock_code      TEXT NOT NULL,
    side            TEXT NOT NULL,
    quantity        INTEGER NOT NULL,
    price           INTEGER,
    state           TEXT NOT NULL,
    order_no        TEXT,
    filled_quantity INTEGER NOT NULL DEFAULT 0,
    reason          TEXT,
    origin          TEXT,
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL,
    unknown_since   TEXT,
    absence_observation_count INTEGER NOT NULL DEFAULT 0,
    absence_first_observed_at TEXT,
    absence_last_observed_at  TEXT,
    released_at     TEXT
);
CREATE INDEX IF NOT EXISTS idx_intents_open
    ON order_intents (stock_code, side, state);
CREATE INDEX IF NOT EXISTS idx_intents_order_no
    ON order_intents (order_no);
-- Ownership is (trading_day, order_no); see `claimed_order_numbers`.
CREATE INDEX IF NOT EXISTS idx_intents_day_order_no
    ON order_intents (trading_day, order_no);
CREATE TABLE IF NOT EXISTS order_intent_audit (
    event_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    intent_id         TEXT NOT NULL,
    event_type        TEXT NOT NULL,
    from_state        TEXT,
    to_state          TEXT,
    reason            TEXT NOT NULL,
    observed_at       TEXT NOT NULL,
    observation_count INTEGER
);
CREATE INDEX IF NOT EXISTS idx_intent_audit_intent
    ON order_intent_audit (intent_id, event_id);
-- NOTE: the (decision_key, attempt) index lives in `_migrate`, not here.
-- On a pre-attempt database the CREATE TABLE above is a no-op and the column
-- does not exist yet, so creating the index here fails the whole open.
"""

_COLUMNS = (
    "intent_id, trading_day, stock_code, side, quantity, price, state, "
    "order_no, filled_quantity, reason, origin, created_at, updated_at, "
    "decision_key, attempt, decision_scope, decision_bucket, unknown_since, "
    "absence_observation_count, absence_first_observed_at, "
    "absence_last_observed_at, released_at"
)


def _to_intent(row: sqlite3.Row | tuple) -> OrderIntent:
    return OrderIntent(
        intent_id=row[0],
        trading_day=row[1],
        stock_code=row[2],
        side=row[3],
        quantity=row[4],
        price=row[5],
        state=row[6],
        order_no=row[7],
        filled_quantity=row[8] or 0,
        reason=row[9],
        origin=row[10],
        created_at=row[11],
        updated_at=row[12],
        decision_key=row[13] or row[0],
        attempt=row[14] or 1,
        decision_scope=row[15],
        decision_bucket=row[16],
        unknown_since=row[17],
        absence_observation_count=row[18] or 0,
        absence_first_observed_at=row[19],
        absence_last_observed_at=row[20],
        released_at=row[21],
    )


# -- ledger -----------------------------------------------------------------


class OrderLedger:
    """SQLite-backed store of order intents.

    Every method raises :class:`OrderLedgerError` on a storage fault rather
    than swallowing it — a ledger that silently stops recording is worse than
    no ledger, because the gates it feeds would quietly open.
    """

    def __init__(
        self,
        path: Path | str | None = DEFAULT_LEDGER_PATH,
        *,
        bucket_seconds: int = DEFAULT_BUCKET_SECONDS,
        mountinfo_reader: Callable[[], str] | None = None,
    ):
        self._path = Path(path) if path is not None else None
        self._bucket_seconds = bucket_seconds
        self._conn: sqlite3.Connection | None = None
        if self._path is None:
            self._storage_safety = LedgerStorageSafety(
                state=STORAGE_LOCAL,
                reason="in-memory ledger has no filesystem backing",
                ledger_path=None,
                metadata_available=False,
            )
        else:
            self._storage_safety = inspect_ledger_storage(
                self._path,
                mountinfo_reader=mountinfo_reader,
            )
            if self._storage_safety.blocks_new_entries:
                raise UnsafeLedgerStorageError(self._storage_safety)
        self._open()

    # -- connection -----------------------------------------------------------

    def _open(self) -> None:
        try:
            if self._path is None:
                self._conn = sqlite3.connect(":memory:", timeout=_BUSY_TIMEOUT_SECONDS)
            else:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                self._conn = sqlite3.connect(
                    str(self._path), timeout=_BUSY_TIMEOUT_SECONDS
                )
                # WAL survives an abrupt kill with the last commit intact,
                # which is the whole point of writing INTENDED before the API
                # call.
                self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=FULL")
            self._conn.execute(
                f"PRAGMA busy_timeout={int(_BUSY_TIMEOUT_SECONDS * 1000)}"
            )
            # Autocommit: registration needs an explicit BEGIN IMMEDIATE so a
            # second process cannot slip between its read and its write.
            self._conn.isolation_level = None
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
            self._migrate()
        except sqlite3.Error as exc:
            self._conn = None
            raise OrderLedgerError(f"ledger open failed: {exc}") from exc

    def _migrate(self) -> None:
        """Bring an older database up to the current shape, non-destructively.

        Only ever adds columns and backfills them; no table is dropped and no
        row is rewritten beyond filling in the new fields. A ledger file is
        the evidence that a duplicate order did not happen, so recreating it
        is never an acceptable migration step.

        Pre-attempt rows are backfilled as ``decision_key = intent_id`` and
        ``attempt = 1``, which is exactly what :func:`make_attempt_id`
        produces for a first attempt — so old ids stay valid.

        Their ``decision_key`` cannot be *recomputed*, though, and that is the
        subtle part. The pre-scope hash was
        ``day|code|side|qty|price|bucket``; today's includes the instruction
        scope, so the same replay now hashes differently and an exact-key
        lookup would miss the legacy row entirely — handing back
        ``may_submit=True`` against a legacy ``UNKNOWN`` or ``FILLED`` order.
        Rewriting the old key to match is not an option either: a settled row
        is the audit record and must stay byte-identical.

        So legacy rows are bridged by the **canonical tuple** instead:
        ``(trading_day, stock_code, side, quantity, price, decision_bucket)``.
        ``decision_bucket`` is backfilled here from ``created_at`` — the same
        timestamp the original key was derived from — and ``decision_scope`` is
        deliberately left ``NULL``, which is what marks a row as pre-scope.
        :meth:`_legacy_bridge_rows` matches only on that marker, so new rows
        keep being distinguished by scope and ``TRIM 5`` still cannot collide
        with ``CUT_LOSS 5``.

        The backfilled bucket assumes ``bucket_seconds`` has not changed since
        the rows were written; it is stored rather than recomputed per query so
        a later default change cannot silently reinterpret history.
        """

        conn = self._require()
        try:
            columns = {
                r[1] for r in conn.execute("PRAGMA table_info(order_intents)")
            }
            if "decision_key" not in columns:
                conn.execute("ALTER TABLE order_intents ADD COLUMN decision_key TEXT")
            if "attempt" not in columns:
                conn.execute(
                    "ALTER TABLE order_intents "
                    "ADD COLUMN attempt INTEGER NOT NULL DEFAULT 1"
                )
            if "decision_scope" not in columns:
                conn.execute(
                    "ALTER TABLE order_intents ADD COLUMN decision_scope TEXT"
                )
            if "decision_bucket" not in columns:
                conn.execute(
                    "ALTER TABLE order_intents ADD COLUMN decision_bucket INTEGER"
                )
            if "unknown_since" not in columns:
                conn.execute(
                    "ALTER TABLE order_intents ADD COLUMN unknown_since TEXT"
                )
            if "absence_observation_count" not in columns:
                conn.execute(
                    "ALTER TABLE order_intents ADD COLUMN "
                    "absence_observation_count INTEGER NOT NULL DEFAULT 0"
                )
            if "absence_first_observed_at" not in columns:
                conn.execute(
                    "ALTER TABLE order_intents ADD COLUMN "
                    "absence_first_observed_at TEXT"
                )
            if "absence_last_observed_at" not in columns:
                conn.execute(
                    "ALTER TABLE order_intents ADD COLUMN "
                    "absence_last_observed_at TEXT"
                )
            if "released_at" not in columns:
                conn.execute(
                    "ALTER TABLE order_intents ADD COLUMN released_at TEXT"
                )
            conn.execute(
                "UPDATE order_intents SET decision_key = intent_id "
                "WHERE decision_key IS NULL OR decision_key = ''"
            )
            conn.execute(
                "UPDATE order_intents SET unknown_since = updated_at "
                "WHERE state = ? AND unknown_since IS NULL",
                (STATE_UNKNOWN,),
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_intents_decision "
                "ON order_intents (decision_key, attempt)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_intents_canonical ON order_intents "
                "(trading_day, stock_code, side, quantity, price, decision_bucket)"
            )
            self._backfill_decision_buckets(conn)
        except sqlite3.Error as exc:
            raise OrderLedgerError(f"ledger migration failed: {exc}") from exc

    def _backfill_decision_buckets(self, conn: sqlite3.Connection) -> None:
        """Derive ``decision_bucket`` for rows that predate the column.

        Only fills NULLs; an existing value is never rewritten. A row whose
        ``created_at`` cannot be parsed is left NULL, which simply means it
        cannot be bridged — the conservative direction, since an unbridged
        legacy row can still be seen by the exact-key path if its key matches.
        """

        rows = list(
            conn.execute(
                "SELECT intent_id, created_at FROM order_intents "
                "WHERE decision_bucket IS NULL"
            )
        )
        for intent_id, created_at in rows:
            stamp = _parse_iso(created_at)
            if stamp is None:
                continue
            conn.execute(
                "UPDATE order_intents SET decision_bucket = ? WHERE intent_id = ?",
                (decision_bucket_for(stamp, self._bucket_seconds), intent_id),
            )

    def close(self) -> None:
        if self._conn is not None:
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            self._conn = None

    @property
    def path(self) -> Path | None:
        return self._path

    @property
    def storage_safety(self) -> LedgerStorageSafety:
        return self._storage_safety

    def _require(self) -> sqlite3.Connection:
        if self._conn is None:
            raise OrderLedgerError("ledger is not open")
        return self._conn

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self._require()
        try:
            cursor = conn.execute(sql, params)
            conn.commit()
            return cursor
        except sqlite3.Error as exc:
            raise OrderLedgerError(f"ledger write failed: {exc}") from exc

    def _query(self, sql: str, params: tuple = ()) -> list[tuple]:
        conn = self._require()
        try:
            return list(conn.execute(sql, params).fetchall())
        except sqlite3.Error as exc:
            raise OrderLedgerError(f"ledger read failed: {exc}") from exc

    # -- writes ---------------------------------------------------------------

    def attempts_for(self, decision_key: str) -> list[OrderIntent]:
        """Every attempt recorded against one decision, oldest first."""

        rows = self._query(
            f"SELECT {_COLUMNS} FROM order_intents "
            "WHERE decision_key = ? ORDER BY attempt",
            (decision_key,),
        )
        return [_to_intent(r) for r in rows]

    def _legacy_bridge_rows(
        self,
        *,
        trading_day: str,
        stock_code: str,
        side: str,
        quantity: int,
        price: int | None,
        bucket: int,
    ) -> list[OrderIntent]:
        """Pre-scope rows for the same decision, found by canonical tuple.

        Their ``decision_key`` was hashed without an instruction scope, so it
        can neither be recomputed nor rewritten (see :meth:`_migrate`). The
        tuple ``(day, code, side, qty, price, bucket)`` is the bridge instead.

        The ``decision_scope IS NULL`` filter is what keeps this from eating
        the scope distinction: only pre-scope rows are ever bridged, so two
        *new* rows with different instructions and the same size stay separate
        decisions.
        """

        return [
            _to_intent(r)
            for r in self._query(
                f"SELECT {_COLUMNS} FROM order_intents "
                "WHERE decision_scope IS NULL AND decision_bucket = ? "
                "AND trading_day = ? AND stock_code = ? AND side = ? "
                "AND quantity = ? AND price IS ? "
                "ORDER BY attempt, created_at",
                (bucket, trading_day, stock_code, side, int(quantity), price),
            )
        ]

    def decision_history(
        self,
        *,
        stock_code: str,
        side: str,
        quantity: int,
        price: int | None,
        decision_scope: str | None = None,
        trading_day: str | None = None,
        now: datetime | None = None,
    ) -> list[OrderIntent]:
        """Every attempt at one decision, legacy rows included, oldest first.

        The audit view of what :meth:`record_intent` reasons over. Rows written
        under the current scheme are found by ``decision_key``; pre-scope rows
        are bridged in by canonical tuple and keep their original keys, so a
        lineage can legitimately span two key values.
        """

        stamp = _now(now)
        day = trading_day or stamp.date().isoformat()
        key = make_decision_key(
            trading_day=day,
            stock_code=stock_code,
            side=side,
            quantity=quantity,
            price=price,
            scope=decision_scope,
            now=stamp,
            bucket_seconds=self._bucket_seconds,
        )
        merged = {i.intent_id: i for i in self.attempts_for(key)}
        for row in self._legacy_bridge_rows(
            trading_day=day,
            stock_code=stock_code,
            side=side,
            quantity=quantity,
            price=price,
            bucket=decision_bucket_for(stamp, self._bucket_seconds),
        ):
            merged.setdefault(row.intent_id, row)
        return sorted(merged.values(), key=lambda i: (i.created_at, i.attempt))

    def record_intent(
        self,
        *,
        stock_code: str,
        side: str,
        quantity: int,
        price: int | None,
        origin: str | None = None,
        decision_scope: str | None = None,
        trading_day: str | None = None,
        now: datetime | None = None,
    ) -> IntentRegistration:
        """Register a decision and, when it is safe, open a new attempt row.

        Returns an :class:`IntentRegistration` whose ``may_submit`` is the
        caller's authorization to touch the order API. Four cases, and the
        distinctions are the whole point:

        ``no prior attempt`` → ``created``
            Insert the next attempt as ``INTENDED``. Submit away.
        ``latest attempt unresolved`` (INTENDED/SUBMITTED/UNKNOWN/OPEN/PARTIAL)
            → ``existing_open``. The identical decision is already in flight;
            re-sending it would duplicate live exposure. The existing row is
            returned for inspection and is **not** modified.
        ``latest attempt FILLED or CANCELLED`` → ``terminal``
            The decision already concluded. Reusing that row as grounds for a
            fresh order both double-trades and destroys the audit record, so
            it is refused outright and the row is left exactly as it is.
        ``latest attempt REJECTED`` → ``created``
            A rejection is proof the broker booked nothing, so a retry is
            safe — but it gets its **own** attempt row and id. The rejected
            row stays as history rather than being overwritten.

        History includes pre-scope rows bridged by canonical tuple, so a
        legacy ``UNKNOWN``/``FILLED`` order still blocks its replay even
        though today's hash of the same decision differs. See
        :meth:`_legacy_bridge_rows`.

        **Atomicity.** The read and the insert run inside one
        ``BEGIN IMMEDIATE`` transaction, so two watchers on the same file
        cannot both conclude "no prior attempt" and both submit. If one still
        wins the race to the primary key, the resulting uniqueness violation
        is re-read and reported as an ordinary duplicate — *not* as a storage
        fault, because the protective-order path treats a fault as "proceed
        anyway" and that would turn a race into a real double sell.
        """

        stamp = _now(now)
        day = trading_day or stamp.date().isoformat()
        bucket = decision_bucket_for(stamp, self._bucket_seconds)
        decision_key = make_decision_key(
            trading_day=day,
            stock_code=stock_code,
            side=side,
            quantity=quantity,
            price=price,
            scope=decision_scope,
            now=stamp,
            bucket_seconds=self._bucket_seconds,
        )
        lookup = dict(
            trading_day=day,
            stock_code=stock_code,
            side=side,
            quantity=quantity,
            price=price,
            bucket=bucket,
        )

        conn = self._require()
        try:
            conn.execute("BEGIN IMMEDIATE")
        except sqlite3.Error as exc:
            raise OrderLedgerError(f"ledger lock failed: {exc}") from exc

        try:
            verdict = self._verdict_for(decision_key, lookup)
            if verdict is not None:
                conn.execute("ROLLBACK")
                return verdict

            history = self._merged_history(decision_key, lookup)
            attempt = (max(i.attempt for i in history) + 1) if history else 1
            intent = self._insert_attempt(
                decision_key=decision_key,
                attempt=attempt,
                trading_day=day,
                stock_code=stock_code,
                side=side,
                quantity=quantity,
                price=price,
                origin=origin,
                decision_scope=decision_scope,
                bucket=bucket,
                stamp=stamp,
            )
            conn.execute("COMMIT")
            return IntentRegistration(
                outcome=REGISTRATION_CREATED, intent=intent
            )
        except sqlite3.IntegrityError:
            # Another connection inserted this very attempt between our read
            # and our write. That is a duplicate, not a broken ledger.
            self._safe_rollback(conn)
            verdict = self._verdict_for(decision_key, lookup)
            if verdict is not None:
                return verdict
            return IntentRegistration(
                outcome=REGISTRATION_EXISTING_OPEN,
                intent=None,
                reason="동일 결정이 다른 프로세스에서 동시 등록됨 — 주문 재전송 안 함",
            )
        except sqlite3.Error as exc:
            self._safe_rollback(conn)
            raise OrderLedgerError(f"ledger write failed: {exc}") from exc

    def _safe_rollback(self, conn: sqlite3.Connection) -> None:
        try:
            conn.execute("ROLLBACK")
        except sqlite3.Error:
            pass

    def _merged_history(
        self, decision_key: str, lookup: dict[str, Any]
    ) -> list[OrderIntent]:
        merged = {i.intent_id: i for i in self.attempts_for(decision_key)}
        for row in self._legacy_bridge_rows(**lookup):
            merged.setdefault(row.intent_id, row)
        return sorted(merged.values(), key=lambda i: (i.created_at, i.attempt))

    def _verdict_for(
        self, decision_key: str, lookup: dict[str, Any]
    ) -> IntentRegistration | None:
        """Refusal for an existing decision, or ``None`` to allow a new attempt."""

        history = self._merged_history(decision_key, lookup)
        if not history:
            return None
        latest = history[-1]
        legacy_note = " (legacy row)" if latest.is_legacy else ""
        if latest.unresolved:
            return IntentRegistration(
                outcome=REGISTRATION_EXISTING_OPEN,
                intent=latest,
                reason=(
                    f"동일 결정의 미종결 attempt 존재 ({latest.state}, "
                    f"attempt {latest.attempt}){legacy_note} — 주문 재전송 안 함"
                ),
            )
        if latest.state in (STATE_FILLED, STATE_CANCELLED) or (
            latest.state == STATE_RELEASED and latest.side != SIDE_SELL
        ):
            return IntentRegistration(
                outcome=REGISTRATION_TERMINAL,
                intent=latest,
                reason=(
                    f"동일 결정이 이미 {latest.state}로 종료 "
                    f"(attempt {latest.attempt}){legacy_note} — 재주문 근거로 쓰지 않음"
                ),
            )
        # REJECTED is a broker verdict and RELEASED is the approved local
        # protective-sell liveness verdict. Both permit a *new* attempt while
        # preserving this row as the prior attempt's audit record.
        return None

    def _insert_attempt(
        self,
        *,
        decision_key: str,
        attempt: int,
        trading_day: str,
        stock_code: str,
        side: str,
        quantity: int,
        price: int | None,
        origin: str | None,
        decision_scope: str | None,
        bucket: int,
        stamp: datetime,
    ) -> OrderIntent:
        intent_id = make_attempt_id(decision_key, attempt)
        iso = stamp.isoformat()
        # Scope is stored as '' rather than NULL when the caller gave none:
        # NULL is reserved to mean "pre-scope legacy row".
        scope = decision_scope or ""
        self._require().execute(
            f"INSERT INTO order_intents ({_COLUMNS}) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                intent_id,
                trading_day,
                stock_code,
                side,
                int(quantity),
                int(price) if price is not None else None,
                STATE_INTENDED,
                None,
                0,
                None,
                origin,
                iso,
                iso,
                decision_key,
                attempt,
                scope,
                bucket,
                None,
                0,
                None,
                None,
                None,
            ),
        )
        return OrderIntent(
            intent_id=intent_id,
            trading_day=trading_day,
            stock_code=stock_code,
            side=side,
            quantity=int(quantity),
            price=int(price) if price is not None else None,
            state=STATE_INTENDED,
            origin=origin,
            created_at=iso,
            updated_at=iso,
            decision_key=decision_key,
            attempt=attempt,
            decision_scope=scope,
            decision_bucket=bucket,
        )

    def mark_state(
        self,
        intent_id: str,
        state: str,
        *,
        order_no: str | None = None,
        filled_quantity: int | None = None,
        reason: str | None = None,
        now: datetime | None = None,
    ) -> None:
        if state not in ALL_STATES:
            raise ValueError(f"unknown intent state: {state!r}")
        if state == STATE_RELEASED:
            raise ValueError(
                "RELEASED is entered only by the UNKNOWN protective-sell "
                "absence policy"
            )
        observed_at = _now(now).isoformat()
        sets = ["state = ?", "updated_at = ?"]
        params: list[Any] = [state, observed_at]
        if state == STATE_UNKNOWN:
            sets.extend(
                [
                    "unknown_since = ?",
                    "absence_observation_count = 0",
                    "absence_first_observed_at = NULL",
                    "absence_last_observed_at = NULL",
                    "released_at = NULL",
                ]
            )
            params.append(observed_at)
        if order_no is not None:
            sets.append("order_no = ?")
            params.append(normalize_order_no(order_no))
        if filled_quantity is not None:
            sets.append("filled_quantity = ?")
            params.append(int(filled_quantity))
        if reason is not None:
            sets.append("reason = ?")
            params.append(reason)
        params.append(intent_id)
        self._execute(
            f"UPDATE order_intents SET {', '.join(sets)} WHERE intent_id = ?",
            tuple(params),
        )

    def apply_order_result(
        self,
        intent_id: str,
        *,
        submitted: bool,
        unknown: bool,
        order_no: str | None,
        reason: str | None,
        now: datetime | None = None,
    ) -> str:
        """Record what the order API told us. Returns the new state.

        Mirrors ``order_result.OrderApplyResult``: accepted → ``SUBMITTED``,
        lost response → ``UNKNOWN`` (never resubmit), rejected →
        ``REJECTED`` (safe to retry, the broker holds nothing).
        """

        current = self.get(intent_id)
        if current is not None and current.state in (
            TERMINAL_STATES | {STATE_OPEN, STATE_PARTIAL}
        ):
            return current.state

        if submitted:
            state = STATE_SUBMITTED
        elif unknown:
            state = STATE_UNKNOWN
        else:
            state = STATE_REJECTED
        self.mark_state(
            intent_id, state, order_no=order_no, reason=reason, now=now
        )
        return state

    # -- reads ----------------------------------------------------------------

    def get(self, intent_id: str) -> OrderIntent | None:
        rows = self._query(
            f"SELECT {_COLUMNS} FROM order_intents WHERE intent_id = ?",
            (intent_id,),
        )
        return _to_intent(rows[0]) if rows else None

    def unresolved(
        self, *, stock_code: str | None = None, side: str | None = None
    ) -> list[OrderIntent]:
        """Intents where the broker may still be holding something."""

        placeholders = ",".join("?" for _ in UNRESOLVED_STATES)
        sql = (
            f"SELECT {_COLUMNS} FROM order_intents "
            f"WHERE state IN ({placeholders})"
        )
        params: list[Any] = sorted(UNRESOLVED_STATES)
        if stock_code is not None:
            sql += " AND stock_code = ?"
            params.append(stock_code)
        if side is not None:
            sql += " AND side = ?"
            params.append(side)
        sql += " ORDER BY created_at"
        return [_to_intent(r) for r in self._query(sql, tuple(params))]

    def has_unresolved(self, stock_code: str, side: str) -> bool:
        return bool(self.unresolved(stock_code=stock_code, side=side))

    def unresolved_codes(self, side: str | None = None) -> set[str]:
        return {i.stock_code for i in self.unresolved(side=side)}

    def unresolved_notional(self, stock_code: str, side: str = SIDE_BUY) -> int:
        """Committed-but-unconfirmed value for a code, for budget gating.

        This is the durable replacement for the old in-memory
        ``_placed_orders`` accumulator.
        """

        return sum(
            i.notional for i in self.unresolved(stock_code=stock_code, side=side)
        )

    def unresolved_sell_quantity(self, stock_code: str) -> int:
        """Shares this process has sell orders out for but not yet confirmed."""

        return sum(
            i.remaining_quantity
            for i in self.unresolved(stock_code=stock_code, side=SIDE_SELL)
        )

    def claimed_order_numbers(self, *, trading_day: str | None = None) -> set[str]:
        """Broker order numbers already attributed to a ledger row.

        **Ownership is per trading day.** Kiwoom order numbers are 7 digits
        (``kiwoom_api_spec.md``) and nothing in the spec makes them unique
        beyond a session — they read as a daily sequence. Treating them as
        globally unique is not merely imprecise, it decays: every terminal row
        the ledger ever wrote would permanently forbid adopting that number
        again, so months in, a growing share of legitimate same-number orders
        would be unmatchable and reconciliation liveness would collapse.

        Scoped to a day, the Task-1 defence is intact — a settled ``FILLED``
        row still owns its number *for that day*, so no later unnumbered
        intent from the same day can adopt it and inherit its fill — while a
        recycled number on a future day is free again.

        ``trading_day=None`` returns every number across all days. That is for
        observability only; it is **not** the ownership predicate.
        """

        if trading_day is None:
            rows = self._query(
                "SELECT order_no FROM order_intents WHERE order_no IS NOT NULL"
            )
        else:
            rows = self._query(
                "SELECT order_no FROM order_intents "
                "WHERE order_no IS NOT NULL AND trading_day = ?",
                (trading_day,),
            )
        return {r[0] for r in rows if r[0]}

    def recent(self, limit: int = 50) -> list[OrderIntent]:
        rows = self._query(
            f"SELECT {_COLUMNS} FROM order_intents "
            "ORDER BY created_at DESC LIMIT ?",
            (int(limit),),
        )
        return [_to_intent(r) for r in rows]

    def audit_events(
        self, intent_id: str | None = None, *, limit: int = 50
    ) -> list[dict[str, Any]]:
        """Append-only policy evidence, newest first.

        The intent row carries the current absence streak for fast restart.
        This table preserves observations that were later reset by an
        incomplete query or a broker row, plus the exact RELEASED transition.
        """

        sql = (
            "SELECT event_id, intent_id, event_type, from_state, to_state, "
            "reason, observed_at, observation_count FROM order_intent_audit"
        )
        params: tuple[Any, ...]
        if intent_id is None:
            sql += " ORDER BY event_id DESC LIMIT ?"
            params = (int(limit),)
        else:
            sql += " WHERE intent_id = ? ORDER BY event_id DESC LIMIT ?"
            params = (intent_id, int(limit))
        rows = self._query(sql, params)
        return [
            {
                "event_id": row[0],
                "intent_id": row[1],
                "event_type": row[2],
                "from_state": row[3],
                "to_state": row[4],
                "reason": row[5],
                "observed_at": row[6],
                "observation_count": row[7],
            }
            for row in rows
        ]

    def _reset_unknown_sell_absence(
        self,
        intent_id: str,
        *,
        reason: str,
        now: datetime | None = None,
    ) -> bool:
        """Reset a protective UNKNOWN sell's current absence streak.

        Returns whether there was evidence to reset. The prior count and reset
        reason remain in the append-only audit table.
        """

        conn = self._require()
        observed_at = _now(now).isoformat()
        try:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT state, side, absence_observation_count "
                "FROM order_intents WHERE intent_id = ?",
                (intent_id,),
            ).fetchone()
            if (
                row is None
                or row[0] != STATE_UNKNOWN
                or row[1] != SIDE_SELL
                or int(row[2] or 0) <= 0
            ):
                conn.execute("ROLLBACK")
                return False
            prior_count = int(row[2] or 0)
            conn.execute(
                "UPDATE order_intents SET absence_observation_count = 0, "
                "absence_first_observed_at = NULL, "
                "absence_last_observed_at = NULL, updated_at = ? "
                "WHERE intent_id = ? AND state = ? AND side = ?",
                (observed_at, intent_id, STATE_UNKNOWN, SIDE_SELL),
            )
            conn.execute(
                "INSERT INTO order_intent_audit "
                "(intent_id, event_type, from_state, to_state, reason, "
                "observed_at, observation_count) VALUES (?,?,?,?,?,?,?)",
                (
                    intent_id,
                    "ABSENCE_RESET",
                    STATE_UNKNOWN,
                    STATE_UNKNOWN,
                    reason,
                    observed_at,
                    prior_count,
                ),
            )
            conn.execute("COMMIT")
            return True
        except sqlite3.Error as exc:
            self._safe_rollback(conn)
            raise OrderLedgerError(
                f"ledger absence-reset write failed: {exc}"
            ) from exc

    def _observe_unknown_sell_absence(
        self, intent_id: str, *, now: datetime | None = None
    ) -> str:
        """Record one complete ka10075+ka10076 absence observation.

        Returns ``ignored``, ``observed`` or ``released``. Only UNKNOWN sells
        are eligible; buys and every other state are immutable here.
        """

        conn = self._require()
        stamp = _now(now)
        observed_at = stamp.isoformat()
        try:
            conn.execute("BEGIN IMMEDIATE")
            raw = conn.execute(
                f"SELECT {_COLUMNS} FROM order_intents WHERE intent_id = ?",
                (intent_id,),
            ).fetchone()
            if raw is None:
                conn.execute("ROLLBACK")
                return "ignored"
            intent = _to_intent(raw)
            if intent.state != STATE_UNKNOWN or intent.side != SIDE_SELL:
                conn.execute("ROLLBACK")
                return "ignored"

            unknown_since = (
                _parse_iso(intent.unknown_since)
                or _parse_iso(intent.updated_at)
                or _parse_iso(intent.created_at)
            )
            if unknown_since is None:
                # No trustworthy start time means no trustworthy grace window.
                conn.execute("ROLLBACK")
                return "ignored"
            age_seconds = (stamp - unknown_since).total_seconds()
            if age_seconds < UNKNOWN_SELL_RELEASE_GRACE_SECONDS:
                conn.execute("ROLLBACK")
                return "ignored"

            previous_at = _parse_iso(intent.absence_last_observed_at)
            if previous_at is not None:
                interval = (stamp - previous_at).total_seconds()
                if interval < UNKNOWN_SELL_RELEASE_MIN_INTERVAL_SECONDS:
                    conn.execute("ROLLBACK")
                    return "ignored"

            count = intent.absence_observation_count + 1
            first_at = intent.absence_first_observed_at or observed_at
            release = count >= UNKNOWN_SELL_RELEASE_MIN_OBSERVATIONS
            if release:
                state = STATE_RELEASED
                reason = (
                    "local protective-sell release: UNKNOWN order absent from "
                    f"{count} complete ka10075+ka10076 observations after "
                    f"{UNKNOWN_SELL_RELEASE_GRACE_SECONDS}s grace; "
                    "broker non-acceptance is not proven"
                )
                event_type = "RELEASED"
            else:
                state = STATE_UNKNOWN
                reason = (
                    "complete ka10075+ka10076 observation found no plausible "
                    "protective sell"
                )
                event_type = "ABSENCE_OBSERVED"

            conn.execute(
                "UPDATE order_intents SET state = ?, updated_at = ?, "
                "absence_observation_count = ?, "
                "absence_first_observed_at = ?, "
                "absence_last_observed_at = ?, released_at = ?, "
                "reason = CASE WHEN ? THEN ? ELSE reason END "
                "WHERE intent_id = ? AND state = ? AND side = ?",
                (
                    state,
                    observed_at,
                    count,
                    first_at,
                    observed_at,
                    observed_at if release else None,
                    1 if release else 0,
                    reason,
                    intent_id,
                    STATE_UNKNOWN,
                    SIDE_SELL,
                ),
            )
            conn.execute(
                "INSERT INTO order_intent_audit "
                "(intent_id, event_type, from_state, to_state, reason, "
                "observed_at, observation_count) VALUES (?,?,?,?,?,?,?)",
                (
                    intent_id,
                    event_type,
                    STATE_UNKNOWN,
                    state,
                    reason,
                    observed_at,
                    count,
                ),
            )
            conn.execute("COMMIT")
            return "released" if release else "observed"
        except sqlite3.Error as exc:
            self._safe_rollback(conn)
            raise OrderLedgerError(
                f"ledger absence-observation write failed: {exc}"
            ) from exc

    # -- reconciliation -------------------------------------------------------

    def reconcile(
        self,
        *,
        open_orders: Iterable[Any] | None = None,
        executions: Iterable[Any] | None = None,
        broker_views_complete: bool = False,
        now: datetime | None = None,
    ) -> ReconcileReport:
        """Resolve unresolved intents against what the broker actually has.

        Matching is by order number where we have one. Where we do not — a
        crash before submit, or a response we lost — matching additionally
        requires a *timestamp* that places the broker event at or after the
        moment we recorded the intent, on the same trading day. Identity
        alone (code, side, quantity, price) is not enough and never was: a
        09:00 fill and a 14:00 lost-response intent for the same stock and
        size look identical, and adopting the former marked the latter
        ``FILLED`` off someone else's trade, releasing the duplicate-order
        block.

        An intent that matches nothing — or matches two things — stays
        unresolved and keeps blocking, except for the approved protective
        UNKNOWN-sell absence policy. ``broker_views_complete`` must be true
        only when both ka10075 and ka10076 completed every pagination page;
        false resets any in-progress sell absence streak.
        """

        report = ReconcileReport()
        pending = self.unresolved()
        report.checked = len(pending)
        if not pending:
            return report

        reference_day = _now(now).date()
        events = _index_broker_rows(
            open_orders, executions, reference_day=reference_day
        )
        # Order-number ownership, keyed by (trading_day, order_no). Loaded per
        # day and cached, so pending intents spanning several trading days
        # never share a claim set — a number owned on Monday must not shadow
        # the same number on Tuesday, and vice versa.
        claimed_by_day: dict[str, set[str]] = {}

        def claimed_for(day: str) -> set[str]:
            if day not in claimed_by_day:
                claimed_by_day[day] = self.claimed_order_numbers(trading_day=day)
            return claimed_by_day[day]

        for intent in pending:
            row = None
            ambiguous = False
            if intent.order_no:
                # Looked up by (day, number), not number alone. A number from
                # our own submit response is ours only within its own session:
                # the 7-digit sequence gets recycled, so a stale intent from a
                # previous day must not bind to today's order that happens to
                # reuse it.
                event = events.by_order_no.get(
                    (intent.trading_day, intent.order_no)
                )
                if event is not None:
                    row = event.row
            else:
                matched, ambiguous = _match_unnumbered(
                    intent, events, claimed_for(intent.trading_day)
                )
                if ambiguous:
                    report.ambiguous.append(intent.intent_id)
                if matched is not None:
                    row = matched.row
                    if matched.order_no:
                        claimed_for(intent.trading_day).add(matched.order_no)
                        report.adopted_order_no += 1

            if row is None:
                if intent.state == STATE_UNKNOWN and intent.side == SIDE_SELL:
                    if not broker_views_complete:
                        if self._reset_unknown_sell_absence(
                            intent.intent_id,
                            reason=(
                                "absence evidence reset: ka10075/ka10076 view "
                                "incomplete (query failure or pagination cap)"
                            ),
                            now=now,
                        ):
                            report.absence_resets += 1
                    elif ambiguous or _possible_broker_presence(intent, events):
                        if self._reset_unknown_sell_absence(
                            intent.intent_id,
                            reason=(
                                "absence evidence reset: plausible broker row "
                                "observed"
                            ),
                            now=now,
                        ):
                            report.absence_resets += 1
                    else:
                        outcome = self._observe_unknown_sell_absence(
                            intent.intent_id, now=now
                        )
                        if outcome == "released":
                            report.released += 1
                            report.resolved += 1
                            continue
                        if outcome == "observed":
                            report.absence_observed += 1
                report.still_unresolved += 1
                report.unmatched.append(intent.intent_id)
                continue

            if intent.state == STATE_UNKNOWN and intent.side == SIDE_SELL:
                if self._reset_unknown_sell_absence(
                    intent.intent_id,
                    reason="absence evidence reset: broker order reconciled",
                    now=now,
                ):
                    report.absence_resets += 1
            state, filled = _classify_broker_row(row, intent)
            self.mark_state(
                intent.intent_id,
                state,
                order_no=normalize_order_no(row.get("ord_no")),
                filled_quantity=filled,
                reason="reconciled",
                now=now,
            )
            if state in TERMINAL_STATES:
                report.resolved += 1
            else:
                report.still_unresolved += 1
        return report


@dataclass(slots=True)
class _BrokerEvent:
    """One broker order row with its identity fields normalized."""

    row: dict[str, Any]
    order_no: str | None
    code: str
    side: str | None
    ordered_qty: int | None
    price: int | None
    at: datetime | None
    trading_day: date | None
    filled_qty: int
    remaining_qty: int | None


@dataclass(slots=True)
class _BrokerEvents:
    # Keyed by ``(trading_day_iso, normalized order_no)`` — the same composite
    # identity ownership uses. A bare number is not a key: 7-digit Kiwoom order
    # numbers are a daily sequence, so two rows sharing one number on
    # different days are different orders and must not be merged.
    by_order_no: dict[tuple[str, str], _BrokerEvent]
    # Deduplicated candidate pool for identity matching: one entry per broker
    # order, plus every row we could not key by number.
    candidates: list[_BrokerEvent]


def _to_event(row: dict[str, Any], *, reference_day: date) -> _BrokerEvent:
    at, day = parse_broker_time(row, reference_day=reference_day)
    return _BrokerEvent(
        row=row,
        order_no=normalize_order_no(row.get("ord_no")),
        code=_normalize_code(row.get("stk_cd")),
        side=row_side(row),
        ordered_qty=_to_int(row.get("ord_qty")),
        price=_to_int(row.get("ord_pric")),
        at=at,
        trading_day=day,
        filled_qty=_to_int(row.get("cntr_qty")) or 0,
        remaining_qty=_to_int(row.get("oso_qty")),
    )


def _prefer(a: _BrokerEvent, b: _BrokerEvent) -> _BrokerEvent:
    """Pick the more advanced of two views of the same broker order.

    The open-order and execution queries routinely both describe one order —
    the same number appears in each with different fill progress. Taking the
    more filled view (ties broken by less remaining) is deterministic and
    cannot regress a settled order back to ``OPEN``, which is what a
    positional "executions win" rule would do if the caller passed the lists
    the other way around.
    """

    if b.filled_qty != a.filled_qty:
        return b if b.filled_qty > a.filled_qty else a
    a_rem = a.remaining_qty if a.remaining_qty is not None else 1 << 30
    b_rem = b.remaining_qty if b.remaining_qty is not None else 1 << 30
    return b if b_rem < a_rem else a


def _index_broker_rows(
    open_orders: Iterable[Any] | None,
    executions: Iterable[Any] | None,
    *,
    reference_day: date,
) -> _BrokerEvents:
    by_order_no: dict[tuple[str, str], _BrokerEvent] = {}
    unnumbered: list[_BrokerEvent] = []
    for source in (open_orders or [], executions or []):
        for row in source:
            if not isinstance(row, dict):
                continue
            event = _to_event(row, reference_day=reference_day)
            if event.order_no is None:
                # Cannot be deduplicated or claimed. Kept as its own
                # candidate, which means two such rows produce ambiguity
                # rather than an arbitrary pick.
                unnumbered.append(event)
                continue
            # Untimed rows come from a same-day query, so they are today's.
            day = (event.trading_day or reference_day).isoformat()
            key = (day, event.order_no)
            existing = by_order_no.get(key)
            by_order_no[key] = (
                event if existing is None else _prefer(existing, event)
            )
    return _BrokerEvents(
        by_order_no=by_order_no,
        candidates=list(by_order_no.values()) + unnumbered,
    )


# How far before an intent's recorded creation time a broker event may sit and
# still be considered the same order. Covers second-granularity broker clocks
# and modest skew; nowhere near enough to let a morning fill match an
# afternoon intent.
MATCH_BACKDATE_TOLERANCE_SECONDS = 60


def _match_unnumbered(
    intent: OrderIntent,
    events: _BrokerEvents,
    claimed: set[str],
) -> tuple[_BrokerEvent | None, bool]:
    """Match an intent that has no broker order number.

    Returns ``(event, ambiguous)``. ``event`` is ``None`` whenever a single
    confident match cannot be made, and ``ambiguous`` says whether that was
    because two or more candidates qualified.

    Every one of these conditions must hold, and each exists to reject a
    specific way of guessing wrong:

    * the order number is not already owned by another ledger row — so a
      settled order's number cannot be re-adopted;
    * code, side and ordered quantity agree, and the price is compatible (an
      intent with no recorded price — a market order — accepts any);
    * the row has a **readable timestamp**. No time, no match: we cannot
      place an untimed row relative to the intent, and guessing is how a
      duplicate happens;
    * the row's trading day equals the intent's. A row from another session
      cannot be this intent's order;
    * the row is not *clearly before* the intent was recorded. The order we
      are looking for was sent microseconds after that write, so anything
      meaningfully earlier is a different order that merely looks the same.
    """

    intent_created = _parse_iso(intent.created_at)
    matches: list[_BrokerEvent] = []
    for event in events.candidates:
        if event.order_no and event.order_no in claimed:
            continue
        if event.code != _normalize_code(intent.stock_code):
            continue
        if event.side != intent.side:
            continue
        if event.ordered_qty != intent.quantity:
            continue
        if intent.price is not None and event.price is not None:
            if event.price != intent.price:
                continue
        # A timestamp is mandatory here (unlike the numbered path): without
        # one we cannot place the row relative to the intent at all.
        if event.at is None or event.trading_day is None:
            continue
        # Day agreement stays mandatory: a row from another session cannot be
        # this intent's order, and it is what makes recycled 7-digit order
        # numbers safe to scope per day.
        if event.trading_day.isoformat() != intent.trading_day:
            continue
        if intent_created is None:
            # We cannot place the intent in time either, so the "not before"
            # test is unavailable and identity alone is not enough.
            continue
        if (
            event.at - intent_created
        ).total_seconds() < -MATCH_BACKDATE_TOLERANCE_SECONDS:
            continue
        matches.append(event)
        if len(matches) > 1:
            break

    if len(matches) == 1:
        return matches[0], False
    if len(matches) > 1:
        log.warning(
            "order ledger: %d broker candidates for intent %s — leaving it "
            "unresolved rather than guessing",
            len(matches),
            intent.intent_id,
        )
        return None, True
    return None, False


def _possible_broker_presence(
    intent: OrderIntent, events: _BrokerEvents
) -> bool:
    """Whether a broker row makes "this sell is absent" unsafe to claim.

    This is deliberately looser than adoption. A row with no timestamp or an
    unreadable side cannot be confidently *matched*, but it is still evidence
    that the two broker views are not clean enough to advance an absence
    streak. Clearly earlier or different-day rows are excluded so an old fill
    does not reset the policy forever.
    """

    intent_created = _parse_iso(intent.created_at)
    for event in events.candidates:
        if event.code != _normalize_code(intent.stock_code):
            continue
        if event.side not in (None, intent.side):
            continue
        if event.ordered_qty not in (None, intent.quantity):
            continue
        if intent.price is not None and event.price is not None:
            if event.price != intent.price:
                continue
        if (
            event.trading_day is not None
            and event.trading_day.isoformat() != intent.trading_day
        ):
            continue
        if (
            event.at is not None
            and intent_created is not None
            and (event.at - intent_created).total_seconds()
            < -MATCH_BACKDATE_TOLERANCE_SECONDS
        ):
            continue
        return True
    return False


def _parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        stamp = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=KST)
    return stamp.astimezone(KST)


# Kiwoom's 주문상태 is free text; these are the substrings that mean a
# terminal outcome regardless of the quantity fields.
_CANCELLED_MARKERS = ("취소",)
_REJECTED_MARKERS = ("거부", "거절")


def _classify_broker_row(
    row: dict[str, Any], intent: OrderIntent
) -> tuple[str, int]:
    """Map one broker row onto an intent state and a filled quantity."""

    status = str(row.get("ord_stt") or "")
    filled = _to_int(row.get("cntr_qty")) or 0
    remaining = _to_int(row.get("oso_qty"))

    if any(marker in status for marker in _CANCELLED_MARKERS):
        return STATE_CANCELLED, filled
    if any(marker in status for marker in _REJECTED_MARKERS):
        return STATE_REJECTED, filled

    if remaining is not None:
        if remaining <= 0:
            # Nothing left working. Filled unless the broker never filled
            # anything, in which case it went away some other way.
            return (STATE_FILLED if filled > 0 else STATE_CANCELLED), filled
        return (STATE_PARTIAL if filled > 0 else STATE_OPEN), filled

    # No remaining-quantity field (some execution rows omit it): fall back to
    # comparing against what we ordered.
    if filled >= intent.quantity > 0:
        return STATE_FILLED, filled
    if filled > 0:
        return STATE_PARTIAL, filled
    return STATE_OPEN, filled


__all__ = [
    "ALL_STATES",
    "DEFAULT_BUCKET_SECONDS",
    "DEFAULT_LEDGER_PATH",
    "LINUX_MOUNTINFO_PATH",
    "LOCAL_FILESYSTEM_TYPES",
    "NETWORK_FILESYSTEM_TYPES",
    "SIDE_BUY",
    "SIDE_CANCEL",
    "SIDE_SELL",
    "STATE_CANCELLED",
    "normalize_stock_code",
    "STATE_FILLED",
    "STATE_INTENDED",
    "STATE_OPEN",
    "STATE_PARTIAL",
    "STATE_REJECTED",
    "STATE_RELEASED",
    "STATE_SUBMITTED",
    "STATE_UNKNOWN",
    "REGISTRATION_CREATED",
    "REGISTRATION_EXISTING_OPEN",
    "REGISTRATION_TERMINAL",
    "TERMINAL_STATES",
    "UNRESOLVED_STATES",
    "UNKNOWN_SELL_RELEASE_GRACE_SECONDS",
    "UNKNOWN_SELL_RELEASE_MIN_INTERVAL_SECONDS",
    "UNKNOWN_SELL_RELEASE_MIN_OBSERVATIONS",
    "IntentRegistration",
    "LedgerStorageSafety",
    "MountInfoEntry",
    "OrderIntent",
    "OrderLedger",
    "OrderLedgerError",
    "ReconcileReport",
    "STORAGE_LOCAL",
    "STORAGE_NETWORK",
    "STORAGE_UNKNOWN",
    "UnsafeLedgerStorageError",
    "classify_ledger_storage",
    "decision_bucket_for",
    "inspect_ledger_storage",
    "make_attempt_id",
    "make_decision_key",
    "normalize_order_no",
    "open_buy_quantity",
    "parse_broker_time",
    "parse_linux_mountinfo",
    "read_linux_mountinfo",
    "open_sell_quantity",
    "row_side",
]
