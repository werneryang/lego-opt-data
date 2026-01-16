# Stock Data Plan

## Scope
- Daily stock data after market close.
- Daily bars (OHLCV).
- Daily IV/HV snapshot and 1-year historical backfill.
- Fundamentals (FMP stable: profile, key-metrics-ttm, ratios-ttm, statements).
- Corporate actions (dividends, splits).
- MCP read-only exposure for downstream consumers.
- Dependencies locked via repo-root `requirements.lock` / `requirements-dev.lock`.
- CI runs from repo root with `make install` and per-subproject lint/test.

## References
- Implementation plan: stock/stock-data/IMPLEMENTATION_PLAN.md
- Monorepo plan: PLAN.md

## Milestones (Draft)
- M1: Stock data scaffolding, config, and universe setup.
- M2: Daily bars + IV/HV pipeline with storage and QA.
- M3: Fundamentals + corporate actions ingestion.
- M4: MCP exposure and operational runbook.
