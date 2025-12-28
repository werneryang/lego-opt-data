# legosmos

Monorepo for market data collection and analysis (options + stocks).

## Projects
- option/opt-data: option chain data acquisition, cleaning, storage, and ops
- option/opt-analysis: option research/backtests/features (placeholder)
- stock/stock-data: stock data acquisition pipeline (placeholder)
- stock/stock-analysis: stock research/backtests (placeholder)
- shared: shared schemas, paths, IO utils, types
- configs: top-level config entrypoint (future; opt-data still uses option/opt-data/config)
- data_lake: shared data root (kept outside repo or gitignored; see README)

## Where to start
- See option/opt-data/README.md for setup and runbook pointers.
- Migration guide: option/opt-data/docs/migration-minimal-downtime.md
