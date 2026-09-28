# Vendored Kiwoom reference data

`kiwoom_request_fields.json` — request-body field names and required flags
for the 21 APIs this repo calls, extracted from the machine-readable spec in
Kiwoom's official API repository (`Kiwoom-Securities/Kiwoom-REST-API`,
`kiwoom/_data/kiwoom_api_spec.json`). The source revision is recorded in the
file's `_source_revision`.

## Why this exists

`kiwoom_api_spec.md` at the repo root is a hand-written transcription and is
incomplete. On 2026-07-28 Phase 0 removed `all_stk_tp` from the ka10075 body
because that table did not list it; the live endpoint rejects the request
without it, and every open-order read failed — silently degrading the
oversell guard, the stale-unfilled cancel path and the UNKNOWN
protective-sell release. All unit tests passed throughout, because they use a
stub client that answers anything.

`tests/test_request_field_conformance.py` checks each request we build
against this data, so a required field cannot be dropped on the strength of
an incomplete table again.

## What it does not settle

The broker is the authority, not this file. It marks kt10001 `ord_uv` as
`Required: N`, yet the broker rejects a 보통 limit without one — that is
exactly what rejected every Tier-2 exit on 2026-08-31 (308003). So the
conformance test asserts one direction only: a field the vendor calls
required must be present. A vendor "optional" proves nothing, and cases like
`ord_uv` are pinned by hand instead.

## Licensing

Kiwoom's package is licensed for use with their service, and forbids
modification and redistribution without written consent. This image is
redistributed to the cluster, so we vendor **reference data** — field names
and required flags, facts about the wire protocol — rather than their code,
and re-express behaviour we want (see `_TOKEN_EXPIRED_CODES` in
`src/services/kiwoom_client.py`) in our own implementation with the source
credited.

## Refreshing

Re-extract from a fresh clone of the upstream repo when adding an API or
after a vendor spec update, and update `_source_revision` and `_retrieved`.
Adding an API to `CASES` in the conformance test is what puts it under guard.
