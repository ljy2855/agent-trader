"""Statistical significance tooling — "is this edge real, or did we fish for it?"

``engine.py`` gives point estimates (expectancy, win rate). ``validate.py``
gives out-of-sample point estimates. Neither says how *uncertain* those
numbers are, nor how much the search itself inflated them. Both gaps are
exactly where retail backtests fool their authors, so this module closes
them with three standard tools:

**1. Bootstrap confidence interval** (`bootstrap_expectancy_ci`)
    Resamples the realized trade list with replacement to get a percentile
    CI on expectancy. Answers "is +0.228%/trade distinguishable from 0?"
    A CI that straddles zero means the point estimate is not evidence of
    an edge, no matter how positive it looks.

**2. Probability of Backtest Overfitting** (`pbo_cscv`)
    Bailey, Borwein, López de Prado & Zhu (2015), via Combinatorially
    Symmetric Cross-Validation. Splits the timeline into S blocks, forms
    every C(S, S/2) in-sample/out-of-sample partition, picks the best
    strategy in-sample in each, and measures how often that winner lands
    in the *bottom half* out-of-sample. PBO is that fraction. High PBO
    (>0.5 = worse than a coin flip) means the selection procedure itself
    is overfitting — the "best" params are best by luck. This tests the
    *process*, not one parameter set, so it's the right lens for a repo
    whose git history shows dozens of tuning passes.

**3. Deflated Sharpe Ratio** (`deflated_sharpe_ratio`)
    Bailey & López de Prado (2014). A Sharpe ratio selected as the max of
    N trials is upward-biased even under a true null of zero skill; DSR
    deflates it by the expected maximum under that null, and also
    corrects for skew/kurtosis. DSR is a probability: > 0.95 is the
    usual "survives multiple testing" bar.

Everything here is pure-stdlib (``statistics.NormalDist`` supplies the
normal CDF/inverse), pure-function, and takes ``engine.Trade`` lists or
plain float sequences — same style as the rest of ``backtest/``, no numpy.

⚠️ These tools quantify *statistical* uncertainty in the simulated trade
list. They cannot detect a flaw shared by every parameter set — a
survivorship-biased universe, a single bull-market regime, or the
engine's next-day-open fill assumption. A low PBO on a fixed 30-name
KOSPI large-cap cache still says nothing about a bear market.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from itertools import combinations
from math import e, isfinite, log, sqrt
from statistics import NormalDist, mean, pstdev

from .engine import Trade

_EULER_MASCHERONI = 0.5772156649015329
_NORM = NormalDist()


# ---------------------------------------------------------------------------
# 1. Bootstrap confidence interval
# ---------------------------------------------------------------------------


@dataclass
class BootstrapCI:
    point: float          # observed expectancy (%/trade)
    lower: float          # CI lower bound
    upper: float          # CI upper bound
    confidence: float     # e.g. 0.95
    n_trades: int
    n_resamples: int
    p_positive: float     # fraction of resamples with expectancy > 0

    @property
    def excludes_zero(self) -> bool:
        """True when the whole interval sits on one side of zero.

        The practical read: False means the data cannot distinguish this
        strategy from "no edge" — the point estimate's sign is noise.
        """
        return (self.lower > 0) or (self.upper < 0)


def bootstrap_expectancy_ci(
    trades: list[Trade],
    *,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 12345,
) -> BootstrapCI | None:
    """Percentile-bootstrap CI for mean net return per trade.

    Resampling *trades* (not calendar days) treats each closed trade as
    the unit of observation, which matches how ``Result.summary()``
    reports expectancy. Returns None for an empty trade list.

    ``seed`` is fixed by default so a given cache + grid always yields the
    same interval — a moving CI would make run-to-run comparisons
    meaningless.
    """
    nets = [t.net_pct for t in trades]
    if not nets:
        return None

    rng = random.Random(seed)
    n = len(nets)
    means: list[float] = []
    for _ in range(n_resamples):
        sample = [nets[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()

    alpha = (1.0 - confidence) / 2.0
    lo_idx = max(0, int(alpha * n_resamples) - 1)
    hi_idx = min(n_resamples - 1, int((1.0 - alpha) * n_resamples))
    return BootstrapCI(
        point=round(sum(nets) / n, 4),
        lower=round(means[lo_idx], 4),
        upper=round(means[hi_idx], 4),
        confidence=confidence,
        n_trades=n,
        n_resamples=n_resamples,
        p_positive=round(sum(1 for m in means if m > 0) / n_resamples, 4),
    )


# ---------------------------------------------------------------------------
# 2. Probability of Backtest Overfitting (CSCV)
# ---------------------------------------------------------------------------


def block_performance(
    trades: list[Trade], block_edges: list[str]
) -> list[float]:
    """Mean net return per time block, bucketed by ``entry_date``.

    ``block_edges`` is a sorted list of S+1 date strings delimiting S
    blocks; block i covers [edges[i], edges[i+1]) with the final block
    closed on the right so the last trade isn't dropped. Blocks with no
    trades score 0.0 — "this strategy sat out" is a real, comparable
    outcome, and dropping the block instead would let a strategy game
    CSCV by trading only in blocks it happens to win.
    """
    n_blocks = len(block_edges) - 1
    sums = [0.0] * n_blocks
    counts = [0] * n_blocks
    for t in trades:
        d = t.entry_date
        for i in range(n_blocks):
            lo, hi = block_edges[i], block_edges[i + 1]
            in_block = (lo <= d < hi) or (i == n_blocks - 1 and d == hi)
            if in_block:
                sums[i] += t.net_pct
                counts[i] += 1
                break
    return [sums[i] / counts[i] if counts[i] else 0.0 for i in range(n_blocks)]


def make_block_edges(all_dates: list[str], n_blocks: int) -> list[str]:
    """Split a sorted date list into ``n_blocks`` equal-length blocks."""
    if n_blocks <= 0 or len(all_dates) < n_blocks:
        raise ValueError(f"need >= {n_blocks} dates, got {len(all_dates)}")
    size = len(all_dates) / n_blocks
    edges = [all_dates[min(int(round(i * size)), len(all_dates) - 1)] for i in range(n_blocks)]
    edges.append(all_dates[-1])
    return edges


@dataclass
class PBOResult:
    pbo: float                    # P(IS-best ranks below OOS median)
    n_blocks: int
    n_splits: int                 # C(S, S/2) combinations evaluated
    n_strategies: int
    logits: list[float]           # λ per split (>0 = winner stayed above median)
    median_oos_rank: float        # mean relative OOS rank of the IS winner (0..1)

    @property
    def verdict(self) -> str:
        if self.pbo >= 0.5:
            return "🔴 과최적화 — IS 우승자가 OOS에서 절반 이상 하위권"
        if self.pbo >= 0.25:
            return "🟡 주의 — 선택 절차가 부분적으로 노이즈를 좇음"
        return "🟢 선택 절차는 OOS로 대체로 전이됨"


def pbo_cscv(
    perf_by_strategy: dict[str, list[float]],
    *,
    n_blocks: int | None = None,
) -> PBOResult | None:
    """Probability of Backtest Overfitting via CSCV.

    ``perf_by_strategy`` maps a strategy label to its per-block
    performance (all lists the same length S, e.g. from
    ``block_performance``). S must be even — CSCV splits blocks into
    equal halves.

    For each of the C(S, S/2) partitions: rank strategies by mean IS
    block performance, take the winner, then find its relative rank ω
    among all strategies' OOS means. λ = logit(ω); PBO = P(λ ≤ 0), i.e.
    the winner failing to beat the OOS median. Returns None if fewer than
    two strategies (PBO is meaningless with nothing to select between).
    """
    labels = list(perf_by_strategy)
    if len(labels) < 2:
        return None
    S = len(perf_by_strategy[labels[0]])
    if n_blocks is not None and n_blocks != S:
        raise ValueError(f"n_blocks={n_blocks} != actual block count {S}")
    if S < 2 or S % 2 != 0:
        raise ValueError(f"CSCV needs an even block count >= 2, got {S}")
    if any(len(v) != S for v in perf_by_strategy.values()):
        raise ValueError("all strategies must share the same block count")

    half = S // 2
    N = len(labels)
    logits: list[float] = []
    ranks: list[float] = []

    for is_idx in combinations(range(S), half):
        is_set = set(is_idx)
        oos_idx = [i for i in range(S) if i not in is_set]

        is_perf = {
            lab: mean(perf_by_strategy[lab][i] for i in is_idx) for lab in labels
        }
        oos_perf = {
            lab: mean(perf_by_strategy[lab][i] for i in oos_idx) for lab in labels
        }
        winner = max(labels, key=lambda lab: is_perf[lab])

        # Relative OOS rank of the IS winner: 1 = best OOS, ~0 = worst.
        # Ties count as half so a flat grid lands at ω≈0.5 (λ≈0) rather
        # than being spuriously pushed to one extreme.
        w = oos_perf[winner]
        below = sum(1 for lab in labels if oos_perf[lab] < w)
        tied = sum(1 for lab in labels if oos_perf[lab] == w) - 1
        omega = (below + 0.5 * tied + 0.5) / N
        omega = min(max(omega, 1e-9), 1 - 1e-9)  # keep logit finite
        ranks.append(omega)
        logits.append(log(omega / (1 - omega)))

    pbo = sum(1 for lam in logits if lam <= 0) / len(logits)
    return PBOResult(
        pbo=round(pbo, 4),
        n_blocks=S,
        n_splits=len(logits),
        n_strategies=N,
        logits=logits,
        median_oos_rank=round(mean(ranks), 4),
    )


# ---------------------------------------------------------------------------
# 3. Deflated Sharpe Ratio
# ---------------------------------------------------------------------------


def _skew_kurt(xs: list[float]) -> tuple[float, float]:
    """Population skewness and (non-excess) kurtosis."""
    n = len(xs)
    m = mean(xs)
    sd = pstdev(xs)
    if sd == 0 or n < 2:
        return 0.0, 3.0
    m3 = sum((x - m) ** 3 for x in xs) / n
    m4 = sum((x - m) ** 4 for x in xs) / n
    return m3 / sd**3, m4 / sd**4


def expected_max_sharpe(n_trials: int, sharpe_variance: float) -> float:
    """E[max Sharpe] across ``n_trials`` independent trials under H0: SR=0.

    Bailey & López de Prado's benchmark: even with zero true skill, the
    best of N tries looks good. This is what a selected Sharpe must clear
    before it counts as evidence.
    """
    if n_trials < 2 or sharpe_variance <= 0:
        return 0.0
    sd = sqrt(sharpe_variance)
    a = _NORM.inv_cdf(1 - 1.0 / n_trials)
    b = _NORM.inv_cdf(1 - 1.0 / (n_trials * e))
    return sd * ((1 - _EULER_MASCHERONI) * a + _EULER_MASCHERONI * b)


@dataclass
class DSRResult:
    sharpe: float             # observed (per-trade) Sharpe
    sharpe_benchmark: float   # E[max Sharpe] under the null, given n_trials
    dsr: float                # probability the true Sharpe exceeds the benchmark
    n_trials: int
    n_obs: int
    skew: float
    kurtosis: float

    @property
    def verdict(self) -> str:
        if self.dsr >= 0.95:
            return "🟢 다중검정 보정 후에도 유의 (DSR ≥ 0.95)"
        if self.dsr >= 0.90:
            return "🟡 경계 — 표본 더 필요 (0.90 ≤ DSR < 0.95)"
        return "🔴 다중검정 보정 후 유의하지 않음 (DSR < 0.90)"


def deflated_sharpe_ratio(
    returns: list[float],
    *,
    n_trials: int,
    trial_sharpes: list[float] | None = None,
) -> DSRResult | None:
    """Deflated Sharpe Ratio for a *selected* strategy's return series.

    ``returns`` are the winning strategy's per-trade net returns (so the
    Sharpe here is per-trade, not annualized — fine, because DSR compares
    it against a benchmark computed on the same scale).

    ``n_trials`` is how many configurations were *effectively* tried. Be
    honest and generous: it should count the whole search, including
    variations explored in past sessions, not just the current grid.
    Under-counting is the classic way to fake a passing DSR.

    ``trial_sharpes`` supplies the cross-trial Sharpe variance. When
    omitted, the variance is approximated as 1/(n_obs-1) — the sampling
    variance of a Sharpe under the null — which is conservative-ish but
    ignores that correlated grid variants inflate the true spread; pass
    the real per-trial Sharpes when you have them.
    """
    n = len(returns)
    if n < 3:
        return None
    sd = pstdev(returns)
    if sd == 0:
        return None
    sr = mean(returns) / sd
    skew, kurt = _skew_kurt(returns)

    if trial_sharpes and len(trial_sharpes) > 1:
        var_sr = pstdev(trial_sharpes) ** 2
    else:
        var_sr = 1.0 / (n - 1)
    sr0 = expected_max_sharpe(n_trials, var_sr)

    denom_sq = 1 - skew * sr + ((kurt - 1) / 4.0) * sr**2
    if denom_sq <= 0 or not isfinite(denom_sq):
        return None
    z = ((sr - sr0) * sqrt(n - 1)) / sqrt(denom_sq)
    return DSRResult(
        sharpe=round(sr, 4),
        sharpe_benchmark=round(sr0, 4),
        dsr=round(_NORM.cdf(z), 4),
        n_trials=n_trials,
        n_obs=n,
        skew=round(skew, 3),
        kurtosis=round(kurt, 3),
    )


__all__ = [
    "BootstrapCI",
    "DSRResult",
    "PBOResult",
    "block_performance",
    "bootstrap_expectancy_ci",
    "deflated_sharpe_ratio",
    "expected_max_sharpe",
    "make_block_edges",
    "pbo_cscv",
]
