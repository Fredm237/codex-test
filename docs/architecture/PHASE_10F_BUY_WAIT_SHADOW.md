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
