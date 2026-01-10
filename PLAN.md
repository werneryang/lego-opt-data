# Monorepo Plan (Top Level)

## Purpose
- Provide cross-project milestones and pointers.
- Detailed execution plans live in each subproject.

## Subproject Plans
- Options pipeline: `option/opt-data/PLAN.md`
- Stock pipeline: `stock/stock-data/IMPLEMENTATION_PLAN.md`

## Cross-Project Milestones (Next 4-8 Weeks)
- Unified dependency locks at repo root for shared environments.
- Stock data MVP: daily bars + daily IV/HV + fundamentals + corporate actions (post-close).
- Stock IV/HV history backfill: 1 year, then daily increments.
- MCP exposure for stock datasets (read-only, consistent with opt-data).
- Stock docs alignment: create `stock/stock-data/docs/` mirroring `option/opt-data/docs`.

## Current Decisions (Stock Pipeline)
- Universe: S&P 500 (separate stock universe file).
- Fundamentals: `ReportsFinStatements`, `ReportRatios`, `Forecasts`, `Ownership` (required).
- Price bars: no adjusted close; record dividends/splits.
- Volatility: daily IV/HV snapshot + 1-year historical backfill.
- Data access: expose via MCP.
