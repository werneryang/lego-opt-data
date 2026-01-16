# Stock Data TODO (Rolling)

## Now
- Expose datasets via MCP (read-only).
- Create ops/dev docs and runbook placeholders.
- Add auto-from-latest backfill option for daily bars and volatility.
- Add daily schedule command for auto backfill runs.
- Add monthly compaction cleanup command to merge price/volatility with logs + verification script.

## Done
- 2026-01-09: Adopt repo-root `requirements.lock` / `requirements-dev.lock` for shared environments.
- Add stock config template (IB settings, paths, schedules).
- Define stock universe file for S&P 500 (symbols + optional conid).
- Implement daily bars fetcher and storage layout.
- Implement IV/HV daily snapshot + 1-year backfill.
- Implement fundamentals ingestion via FMP stable + cache.
- Add ratios-ttm for pe_ttm/eps_ttm parsing.
- Add corporate actions ingestion and storage.
- Add remote config and verify daily bars + volatility smoke tests.
