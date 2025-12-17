Weekend History Backfill Implementation Walkthrough
Summary
Implemented 
weekend_history_backfill.py
 per 
requirements
.

Script Features
Feature	Implementation
Contracts Cache	
load_latest_contracts_cache()
 - reads state/contracts_cache/{SYMBOL}_*.json, takes latest by date
Active Subset	
filter_active_subset()
 - filters to top E expiries × K strikes per side
Hours Stage	Full contracts, 8 hours bars, 6 M duration
Minutes Stage	Active subset only, 30 mins bars, 1 M duration
Batch Support	--batch-index/--batch-count using 
stable_batch_slice()
Resume	Skips contracts with existing Parquet output
Output	Parquet to data_test/raw/ib/historical_bars_weekend/
Summary	JSONL to state/run_logs/historical_backfill/
Verification Results
Syntax & Lint
✓ ruff check --select=E,F → All checks passed
✓ py_compile → Syntax OK
Dry-run Tests
Hours stage with history universe:

python scripts/weekend_history_backfill.py \
  --stage hours \
  --universe config/universe_history_202511.csv \
  --batch-count 8 --batch-index 0 --dry-run
Plan: stage=hours symbols_total=382 batch=1/8 symbols_batch=48
TSLA: 340 contracts (cache: 2025-12-11)
AAPL: 344 contracts (cache: 2025-12-11)
Minutes stage:

python scripts/weekend_history_backfill.py \
  --stage minutes --symbols "AAPL" \
  --top-expiries 3 --strikes-per-side 2 --dry-run
Plan: stage=minutes symbols_total=1 batch=1/1 symbols_batch=1
AAPL: 344 contracts (cache: 2025-12-11)
Usage Reference
# Hours: Full contracts for batch 0 of 8
python scripts/weekend_history_backfill.py \
  --stage hours \
  --universe config/universe_history_202511.csv \
  --batch-count 8 --batch-index 0 \
  --port 4002
# Minutes: Active subset only
python scripts/weekend_history_backfill.py \
  --stage minutes \
  --symbols "AAPL,MSFT" \
  --top-expiries 5 --strikes-per-side 3 \
  --port 4002
# Resume interrupted run
python scripts/weekend_history_backfill.py \
  --stage hours --symbols "AAPL" --resume
Next Steps
Run actual hours stage with IB Gateway connected
Verify Parquet output with pd.read_parquet()
Run minutes stage after hours completes
Generate rerun universe from summary JSONL for failed symbols