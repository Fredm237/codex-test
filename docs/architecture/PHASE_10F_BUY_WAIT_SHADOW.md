# Phase 10F — BUY/WAIT V2 shadow persistence

## Boundary

`buy_wait_decision_runs` is an additive, append-only projection sourced from a
persisted Confidence run. It stores only references, aggregates, reason codes,
claims, evidence references and deterministic digests. Raw user context and
future observations are forbidden by both the writer and database constraints.

An action row is valid only with a selected offer and product, current price and
currency, at least eight historical samples over fourteen days, a calibrated
Decision Confidence, a temporal backtest profile and evidence-bearing claims.
Otherwise the engine persists an honest `ABSTAIN` with no backtest identity.

## Replay

`python -m app.buy_wait.replay` requires an explicit timestamp and a bounded
window of at most 100 Confidence runs. Dry-run is the default. Apply requires
`BUY_WAIT_SHADOW_ENABLED=true`; the flag is OFF by default and depends on the
Confidence shadow. Repeating the same window with the same timestamp resolves
to the existing deterministic row.

The first production qualification is expected to abstain because the current
production Confidence sample has no ratified per-product temporal profile. This
is the intended fail-closed outcome, not a fabricated BUY or WAIT action.

No public reader, API endpoint or persistent product flag is connected to this
table in Phase 10.

## Production qualification

The additive migration reached production at revision `f3c1e5a7b9d2` through
Railway deployment `dd723950-6c51-4f14-8442-9d177e0b8ef0`.

One strictly bounded window was evaluated at `2026-09-01T20:45:00Z`, starting
after Confidence run 0 with limit 1. Dry-run, unique apply and identical replay
all produced the same evaluation identity:
`sha256:cd12a5ebbe0e0aa14eaeb50c08cd479c87156e83358a136ac4bf9da62e515a7a`.

The unique apply scanned one source run, created one append-only row and
returned `ABSTAIN`. The identical replay scanned the same source, created zero
rows and resolved one existing row. This is the expected fail-closed result for
a source without a ratified temporal profile.

All twelve persistent shadow flags, from Observation through Buy/Wait, were
read back as `false` after qualification. No Railway variable or public reader
was changed.
