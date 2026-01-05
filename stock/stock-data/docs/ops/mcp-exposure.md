# MCP Exposure Plan (Stock Data)

## Scope
Read-only access to stock datasets for analytics and operations. No IB access and no writes.

## Datasets
Clean:
- `clean.stock.daily_bars`
- `clean.stock.volatility`
- `clean.stock.fundamentals`
- `clean.stock.corporate_actions`

Raw (optional, gated by `allow_raw=true`):
- `raw.stock.daily_bars`
- `raw.stock.volatility`
- `raw.stock.fundamentals`
- `raw.stock.corporate_actions`

## Filters
- `date` (single day) or `date_start`/`date_end` (bounded range)
- `symbol` (single) or `symbols` (list)
- `exchange` (default `SMART`)
- `report_type` (fundamentals only)

## Limits and Permissions
- Default `limit=200`, max `limit=2000`.
- Default `days=3`, max `days=14`.
- `allow_clean=true` required for `clean.*` datasets.
- `allow_raw=true` required for `raw.*` datasets.
- Tool-specific hard caps:
  - `fundamentals`: max 500 rows
  - `corporate_actions`: max 1000 rows
  - `daily_bars` and `volatility`: max 2000 rows

## Audit Fields
Audit entries are stored in `mcp_audit_log`:
- `timestamp`
- `tool_name`
- `params` (JSON)
- `rows_returned`
- `duration_ms`
- `status`
- `error`

## Notes
- Responses include `meta` with `limit`, `clamped`, and `source`.
- Default audit DB: `state/run_logs/mcp_audit.db`.
