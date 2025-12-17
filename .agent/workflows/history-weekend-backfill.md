# Workflow: Weekend History Backfill (Experimental)

This workflow captures the dev-only plan to backfill IBKR option historical bars in batches, using existing contracts cache.

## Scope
- Dev/data_test only; not part of production schedule.
- Contract universe comes from the latest available `contracts_cache` per symbol.
- `TRADES` only; no automatic fallback to `MIDPOINT` when no data.

## Stages
- `hours`: full cached contract set; start with `8 hours` + `6 M` (useRTH).
- `minutes`: **ATM subset** only (K strikes per right per expiry, E expiries); start with `30 mins` + `1 M` (useRTH).

## Operational Notes
- Always run with batch slicing (`--batch-count/--batch-index`) and conservative pacing.
- Emit a JSONL summary per run and generate rerun universe CSV for `ERR/EMPTY`.

## Source of Truth
- Detailed requirement spec: `docs/dev/history-weekend-backfill.md`

