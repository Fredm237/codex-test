# FILON — Phase 10 Buy/Wait v2 Final Receipt

- Date: **1 September 2026**
- Decision: **PHASE 10 = GO**
- Mode: **shadow append-only, fail-closed**
- Public readers: **OFF**
- Persistent shadow flags: **OFF**

## Delivery evidence

- source branch: `codex/filon-phase-10-buy-wait-v2`;
- authorized source commit: `59cdeb16ddf7f1afc0c372569c786b8cd19cd554`;
- metadata registration fix: remote commit
  `c0204ae6f83b18d4934283f5b2e2c86a07926625`;
- pull request: GitHub `#409`, terminally merged;
- merge commit: `2e83e60d2a20a7d11a7fdf6186eb5b7158f1dede`;
- terminal CI: run `33556977047`, four jobs successful;
- Railway qualification deployment:
  `dd723950-6c51-4f14-8442-9d177e0b8ef0`;
- production Alembic revision: `f3c1e5a7b9d2`.

The public branch tree was verified identical to the qualified local tree. The
protected backend README, Python version and project manifest were not included
in the Phase 10 change set. No secret, user data, raw context or raw offer
payload was published.

## Quality Lab receipt

The autonomous temporal backtest evaluated 7,200 deterministic cases across
six verticals, three locales and four seeds. Of those, 3,600 were actionable.
Action accuracy was 1.0, the Wilson lower bound was 0.99893407, and
wrong-direction actions, unsupported actions and future leakage were all zero.
Evidence and provenance coverage were complete.

Evaluation identity:
`sha256:168f576a06ba362161629bc358519a25b8a4fde3cf3ea29be270f8b4872ad187`.

## Production shadow receipt

The qualification used one explicit and strictly bounded source window:

- `evaluated_at=2026-09-01T20:45:00Z`;
- `after_confidence_run_id=0`;
- `limit=1`.

| Pass | Scanned | Decision | Created | Existing |
|---|---:|---|---:|---:|
| dry-run | 1 | `ABSTAIN` | 0 | 0 |
| unique apply | 1 | `ABSTAIN` | 1 | 0 |
| identical replay | 1 | `ABSTAIN` | 0 | 1 |

All three passes produced evaluation identity
`sha256:cd12a5ebbe0e0aa14eaeb50c08cd479c87156e83358a136ac4bf9da62e515a7a`.
The abstention is honest: the production sample has no ratified per-product
temporal profile. No BUY or WAIT action was fabricated.

After the replay, all twelve persistent shadow flags were read back as `false`.
No public API reader is connected to the new table.

## Production snapshot

- `/health/live`: alive;
- `/health/ready`: ready, PostgreSQL healthy, schema `f3c1e5a7b9d2`;
- `/health`: application, PostgreSQL and Redis healthy; Qdrant disabled by
  configuration;
- `/api/catalog/highlights`: HTTP 200 with explicit currencies and current
  evidence; observed response time about 34 seconds;
- Railway web, PostgreSQL and Redis services: online;
- catalog Cron: normal cadence, no second live ingestion observed.

The catalog pulse retains run 23 as `running` with a stale heartbeat and
`recovery_required=true`. Railway has no corresponding live Cron process, so
this is a recoverable historical journal state rather than a concurrent writer.
It predates and is independent of Buy/Wait qualification.

## Limitations carried forward

1. `AUTONOMOUS_QUALITY_LAB` is engineering evidence, not independent commercial
   ground truth. Status remains
   `NO_EXTERNAL_HUMAN_GROUND_TRUTH / NON_BLOCKING` and
   `NOT_INDEPENDENTLY_VALIDATED`.
2. Phase 10 predicts neither a future price nor a date or guaranteed saving.
3. Production correctly abstains without a ratified temporal profile.
4. Catalog highlights is operational but currently slow under the production
   corpus; this is a performance follow-up, not a Buy/Wait integrity blocker.
5. The stale catalog journal entry should be reconciled by the existing
   fail-closed recovery path without launching concurrent ingestion.

## Gate decision

Contracts, deterministic policy, temporal isolation, backtest gates, additive
migration, append-only persistence, bounded production replay and idempotency
are proven. The system remained dark to public readers and all persistent flags
remained OFF.

**PHASE 10 = GO.**
