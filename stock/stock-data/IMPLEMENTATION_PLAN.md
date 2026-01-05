# Stock Data Collection - Implementation Requirements and Plan

## 1. Background and Current Project Structure

- Repository layout: monorepo with `option/opt-data` (active), `stock/stock-data` (placeholder), and shared roots (`shared`, `configs`, `data_lake`).
- `option/opt-data` is a production-ready pipeline for options with:
  - IB access via `ib_insync` (`src/opt_data/ib/`), rate limiting, discovery, snapshot, and historical fetch.
  - Pipeline stages: `snapshot` (intraday), `rollup` (EOD), `enrichment` (T+1).
  - Scheduling via `ScheduleRunner` with ET timezone conventions.
  - Storage conventions: Parquet, partitioned by `date/underlying/exchange`, raw vs clean layers.
  - Operational docs and data contract in `option/opt-data/docs/`.
- Existing probes for stock IV are already in scripts:
  - `scripts/stk_iv_tick106_probe.py` (reqMktData + generic tick 106).
  - `scripts/stk_iv_history_probe.py` (reqHistoricalData with IV/HV).

## 2. Goals and Scope

### Goals
- Add stock data collection with a daily (post-close) run.
- Data includes:
  - Daily trading bars (OHLCV).
  - Fundamentals (IB fundamental reports).
  - Daily IV and historical volatility (current day + history).
- Universe: S&P 500 (initially from existing `config/universe.csv`).
- Data source: IB Gateway (subscription already in place).
 - Expose datasets via MCP for downstream consumers.

### Out of Scope (for now)
- Intraday bar streaming.
- Non-US markets.
- Alternative data sources outside IB.

## 3. Requirements

### Functional Requirements
1. **Daily price bars**: fetch daily OHLCV for each symbol.
2. **Daily IV/HV**:
   - Same-day IV/HV snapshot after close.
   - Historical IV/HV backfill (1 year) and daily incremental updates.
3. **Fundamentals**:
   - Fetch required report types per symbol daily:
     - `ReportsFinStatements`
     - `ReportRatios`
     - `Forecasts`
     - `Ownership`
   - Optional: `ReportSnapshot` if it provides fields not covered above.
4. **Scheduling**:
   - Run once per trading day after market close (e.g., 17:30 ET).
5. **Storage**:
   - Raw and clean outputs with consistent partitioning.
6. **Integration**:
   - Reuse IB session, rate limiting, logging, and QA patterns.
7. **Corporate actions**:
   - Record dividends/splits and link them to daily bars and fundamentals.

### Non-Functional Requirements
- Retry and pacing safety compatible with IB limits.
- Deterministic, idempotent writes per day.
- Clear data contract and schema versioning.
- Operator-friendly logs and QA summary.

## 4. Data Sources and IB API Mapping

### Daily Price Bars
- API: `reqHistoricalData`
  - `whatToShow="TRADES"`
  - `barSizeSetting="1 day"`
  - `durationStr="N D"`
  - `useRTH=True`
Note: no adjusted close is required for this phase.

### IV/HV
- **Same-day IV**: `reqMktData` + `genericTicks=106` (tickType 24).
- **Historical IV/HV**: `reqHistoricalData`
  - `whatToShow="OPTION_IMPLIED_VOLATILITY"` and `"HISTORICAL_VOLATILITY"`
  - `barSizeSetting="1 day"`

Note: validate availability per symbol and subscription; fallback to `useRTH=True` or reduced durations when needed.

### Fundamentals
- API: Financial Modeling Prep (FMP)
  - Report types mapped to FMP endpoints: `info`, `financials`, `balance_sheet`, `cashflow`, `calendar`,
    `institutional_holders`, `major_holders`.
  - Store raw JSON payloads and a minimal normalized table for common fields.

## 5. Proposed Data Contract and Storage Layout

### Storage Roots (proposed)
- Raw: `data/raw/ib/stk`
- Clean: `data/clean/ib/stk`

### Partition Keys
- `date=<YYYY-MM-DD>`
- `symbol=<SYMBOL>`
- `exchange=<EXCHANGE>`

### Datasets
1. **Daily bars** (`view=daily_bars`)
   - Keys: `trade_date`, `symbol`, `exchange`
   - Fields: `open`, `high`, `low`, `close`, `volume`, `barCount`, `wap`, `asof_ts`, `source`
2. **Daily IV/HV** (`view=volatility`)
   - Keys: `trade_date`, `symbol`
   - Fields: `iv_30d`, `hv_30d` (or `iv`, `hv`), `asof_ts`, `source`, `market_data_type`
3. **Fundamentals** (`view=fundamentals`)
   - Keys: `asof_date`, `symbol`, `report_type`
   - Raw payload: `raw_json`
   - Normalized fields: `market_cap`, `pe_ttm`, `eps_ttm`, `sector`, `industry`
4. **Corporate actions** (`view=corporate_actions`)
   - Keys: `event_date`, `symbol`, `event_type`
   - Fields: `ratio`, `cash_amount`, `notes`, `source`, `asof_ts`

## 6. Architecture and Integration Recommendations

### Recommended Approach
- Create a new package under `stock/stock-data` modeled after `option/opt-data`.
- Reuse shared concepts and patterns:
  - IB connection wrapper and rate limiting.
  - Storage writer and partition layout.
  - Schedule runner pattern (daily after close).
  - MCP exposure pattern for dataset access.

### Integration Options
**Option A (Preferred):** new `stock-data` service
- Clear separation from options pipeline.
- Reuse helpers by copying or moving shared utilities to `shared/`.

**Option B (Short-term):** extend `option/opt-data`
- Faster to ship but mixes domains and naming.

## 7. Implementation Plan

### Phase 0 - Decisions and Design (1-2 days)
- Confirm datasets, fields, and report types for fundamentals.
- Define storage paths and partitioning scheme.
- Decide whether to split into `stock/stock-data` or extend `opt-data`.

### Phase 1 - Scaffolding (1-2 days)
- Create `stock/stock-data` Python package structure:
  - `ib/`, `pipeline/`, `storage/`, `cli.py`, `config.py`, `tests/`
- Add configuration file (modeled after `opt-data`).
- Implement `IBSession` wrapper (reuse or copy).

### Phase 2 - Daily Price Bars (2-3 days)
- Implement `stock_data.ib.history.fetch_daily_bars`.
- Implement pipeline runner:
  - Load universe (S&P 500).
  - Fetch and write daily bars.
- Add CLI: `python -m stock_data.cli daily --date today`.

### Phase 3 - IV/HV (2-3 days)
- Implement `reqMktData` snapshot for daily IV.
- Implement historical IV/HV fetcher (1-year backfill) and daily incremental update.
- Persist to `view=volatility`.

### Phase 4 - Fundamentals (2-4 days)
- Implement fundamental data fetcher.
- Store raw XML and parse minimal normalized fields.
- Add a QA check for missing reports.
 - Add corporate actions ingestion (dividends/splits) and link to daily bars.

### Phase 5 - Scheduling and Ops (1-2 days)
- Add a scheduler entry for post-close run (17:30 ET).
- Add logging, metrics, and run logs.
- Update ops runbook for stock pipeline.

### Phase 6 - Validation and Backfill (2-3 days)
- Run AAPL/MSFT smoke test.
- Backfill last N days for S&P 500.
- Validate coverage and data quality thresholds.

## 8. Testing and QA

- Unit tests for parsing, schema validation, and storage.
- Smoke tests against IB Gateway for a small universe.
- QA checks:
  - Missing rate per field.
  - IV/HV range checks.
  - Daily bar completeness per symbol.

## 9. Risks and Dependencies

- IB pacing or subscription gaps causing partial coverage.
- Fundamental data coverage varies by symbol.
- IV/HV availability may be inconsistent for some equities.
- Scheduling after close must respect trading calendar and early close days.

## 10. Open Questions

1. Exact schema and priority fields for the fundamentals normalization table?
2. Where should stock pipeline docs live (mirror `option/opt-data/docs` under `stock/stock-data/docs`)?
3. Should MCP exposure be added to the existing MCP server or a dedicated stock MCP server?
