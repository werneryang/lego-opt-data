# Stock Data Contract (Draft)

## Overview
- Data root: `data_lake` is the shared data lake root (gitignored). You can also point configs to an external absolute path.
- Views:
  - `data_lake/stock/raw/ib/stk/view=daily_bars`
  - `data_lake/stock/raw/ib/stk/view=volatility`
  - `data_lake/stock/raw/ib/stk/view=fundamentals`
  - `data_lake/stock/raw/ib/stk/view=corporate_actions`
  - `data_lake/stock/clean/ib/stk/view=daily_bars`
  - `data_lake/stock/clean/ib/stk/view=volatility`
  - `data_lake/stock/clean/ib/stk/view=fundamentals`
  - `data_lake/stock/clean/ib/stk/view=corporate_actions`
- Partitions: `date` (trade date, ET), `symbol`, `exchange`, `view`.
- File format: Parquet with hot/cold codec policy.

## Shared Fields
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `trade_date` | `date` | yes | Trading date in ET |
| `symbol` | `string` | yes | Uppercase symbol |
| `exchange` | `string` | yes | Default `SMART` |
| `source` | `string` | yes | `IBKR` |
| `asof_ts` | `timestamp[ns]` | yes | UTC timestamp |
| `ingest_id` | `string` | yes | UUID |
| `ingest_run_type` | `string` | yes | `eod` |
| `market_data_type` | `int32` | no | 1=live, 2=frozen, 3=delayed, 4=delayed-frozen |
| `data_quality_flag` | `list<string>` | no | e.g. `delayed_fallback` |

## Daily Bars (view=daily_bars)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `open` | `double` | yes | Daily open |
| `high` | `double` | yes | Daily high |
| `low` | `double` | yes | Daily low |
| `close` | `double` | yes | Daily close |
| `volume` | `int64` | yes | Daily volume |
| `barCount` | `int64` | no | IB bar count |
| `wap` | `double` | no | Weighted average price |

## Volatility (view=volatility)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `iv_30d` | `double` | yes | Tick 106 (30D IV) |
| `hv_30d` | `double` | no | `HISTORICAL_VOLATILITY` |
| `source_ts` | `timestamp[ns]` | no | Optional raw timestamp |

## Fundamentals (view=fundamentals)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `report_type` | `string` | yes | `info`, `financials`, `balance_sheet`, `cashflow`, `calendar`, `institutional_holders`, `major_holders` |
| `asof_date` | `date` | no | As reported |
| `raw_json` | `string` | yes | Raw JSON payload (FMP) |
| `market_cap` | `double` | no | Parsed field (info) |
| `pe_ttm` | `double` | no | Parsed field (info) |
| `eps_ttm` | `double` | no | Parsed field (info) |
| `sector` | `string` | no | Parsed field (info) |
| `industry` | `string` | no | Parsed field (info) |

### Fundamentals Report Types and Endpoints
Base URL: `https://financialmodelingprep.com/stable` (see `FundamentalsRunner._fetch_report` in `stock/stock-data/src/stock_data/pipeline/fundamentals.py`).

| `report_type` | FMP endpoint(s) | Params | Notes |
| --- | --- | --- | --- |
| `info` | `/profile`, `/key-metrics-ttm`, `/ratios-ttm` | `symbol`, `apikey` | Combines profile + metrics_ttm + ratios_ttm into one payload. |
| `financials` | `/income-statement` | `symbol`, `limit`, `apikey` | Default `limit=4`. |
| `balance_sheet` | `/balance-sheet-statement` | `symbol`, `limit`, `apikey` | Default `limit=4`. |
| `cashflow` | `/cash-flow-statement` | `symbol`, `limit`, `apikey` | Default `limit=4`. |
| `calendar` | `/earnings-calendar` | `apikey` | Calendar is not symbol-scoped in current logic. |
| `institutional_holders` | `/institutional-holder` | `symbol`, `apikey` | Symbol-scoped. |
| `major_holders` | `/major-holders` | `symbol`, `apikey` | Symbol-scoped. |

## Corporate Actions (view=corporate_actions)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `event_date` | `date` | yes | Dividend/split effective date |
| `event_type` | `string` | yes | `dividend`, `split`, `spinoff` |
| `ratio` | `double` | no | Split ratio |
| `cash_amount` | `double` | no | Dividend amount |
| `notes` | `string` | no | Freeform notes |

## Quality Checks (Draft)
- Daily bars: `open/high/low/close` non-null, `volume >= 0`.
- Volatility: `iv_30d` in `[0, 10]`, `hv_30d` in `[0, 10]` if present.
- Fundamentals: required report types present per symbol, XML non-empty.
- Corporate actions: events are recorded with `event_date` and `event_type`.

## Scheduling
- Daily run after market close (default 17:30 ET).
- Volatility history backfill: 1 year, then incremental daily updates.

## Production Migration Checklist (iMac)
- Repo root: `/users/michaely/projects/legosmos`
- Data lake root: `/users/michaely/projects/legosmos/data_lake` (gitignored; use absolute paths on production)
- Config: use `stock/stock-data/config/stock-data.toml` or a local copy (keep untracked) and set absolute paths:
- If using a local config, confirm `config/stock-data.local.toml` exists (otherwise `cp config/stock-data.toml config/stock-data.local.toml`).

```toml
[paths]
raw = "/users/michaely/projects/legosmos/data_lake/stock/raw/ib/stk"
clean = "/users/michaely/projects/legosmos/data_lake/stock/clean/ib/stk"
state = "/users/michaely/projects/legosmos/stock/stock-data/state"
```

- Environment: `FMP_API_KEY` for fundamentals; `TZ=America/New_York` for scheduling consistency
- IB Gateway: local `127.0.0.1:4001` if running `daily-bars` or `volatility`
- Smoke test:
  - `python -m stock_data.cli inspect --config config/stock-data.toml`
  - `python -m stock_data.cli fundamentals --config config/stock-data.toml --symbols AAPL --report-types info --max-symbols 1`
