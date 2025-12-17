#!/bin/bash
#
# Weekend History Backfill Runner
#
# Usage:
#   ./scripts/run_weekend_backfill.sh           # Run all batches
#   ./scripts/run_weekend_backfill.sh --hours   # Run hours stage only
#   ./scripts/run_weekend_backfill.sh --minutes # Run minutes stage only
#   ./scripts/run_weekend_backfill.sh --batch 2 # Run specific batch (0-7)
#
# Prerequisites:
#   - Remote IB Gateway running at REMOTE_HOST:REMOTE_PORT
#   - Latest contracts cache in state/contracts_cache/
#
# Output:
#   - Parquet: data_test/raw/ib/historical_bars_weekend/{SYMBOL}/{conId}/TRADES/
#   - Summary: state/run_logs/historical_backfill/summary_*.jsonl
#

set -e

# Configuration
REMOTE_HOST="${IB_HOST:-100.71.7.100}"
REMOTE_PORT="${IB_PORT:-4001}"
CLIENT_ID="${IB_CLIENT_ID:-220}"
UNIVERSE="config/universe_history_202511.csv"
BATCH_COUNT=8
BATCH_SLEEP=60  # seconds between batches

# Parse arguments
RUN_HOURS=true
RUN_MINUTES=true
SPECIFIC_BATCH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --hours)
            RUN_MINUTES=false
            shift
            ;;
        --minutes)
            RUN_HOURS=false
            shift
            ;;
        --batch)
            SPECIFIC_BATCH="$2"
            shift 2
            ;;
        --host)
            REMOTE_HOST="$2"
            shift 2
            ;;
        --port)
            REMOTE_PORT="$2"
            shift 2
            ;;
        --client-id)
            CLIENT_ID="$2"
            shift 2
            ;;
        --universe)
            UNIVERSE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--hours] [--minutes] [--batch N] [--host HOST] [--port PORT] [--client-id ID] [--universe FILE]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo "================================================"
echo "Weekend History Backfill Runner"
echo "================================================"
echo "Remote Gateway: ${REMOTE_HOST}:${REMOTE_PORT}"
echo "Client ID: ${CLIENT_ID}"
echo "Universe: ${UNIVERSE}"
echo "Batch count: ${BATCH_COUNT}"
echo "Run hours: ${RUN_HOURS}"
echo "Run minutes: ${RUN_MINUTES}"
echo "Specific batch: ${SPECIFIC_BATCH:-all}"
echo "================================================"

# Test connection first
echo ""
echo "Testing IB Gateway connection..."
python -c "
from ib_insync import IB
ib = IB()
try:
    ib.connect('${REMOTE_HOST}', ${REMOTE_PORT}, clientId=${CLIENT_ID}, timeout=10)
    print('✓ Connection successful')
    ib.disconnect()
except Exception as e:
    print(f'✗ Connection failed: {e}')
    exit(1)
"

# Run hours stage
if [ "$RUN_HOURS" = true ]; then
    echo ""
    echo "================================================"
    echo "Running HOURS stage ($BATCH_COUNT batches)"
    echo "================================================"
    
    if [ -n "$SPECIFIC_BATCH" ]; then
        batches="$SPECIFIC_BATCH"
    else
        batches=$(seq 0 $((BATCH_COUNT - 1)))
    fi
    
    for i in $batches; do
        echo ""
        echo "--- Hours batch $((i + 1))/${BATCH_COUNT} ---"
        python scripts/weekend_history_backfill.py \
            --stage hours \
            --universe "$UNIVERSE" \
            --batch-count "$BATCH_COUNT" \
            --batch-index "$i" \
            --host "$REMOTE_HOST" \
            --port "$REMOTE_PORT" \
            --client-id "$CLIENT_ID" \
            --historical-per-minute 10 \
            --historical-burst 5 \
            --resume
        
        if [ "$i" -lt $((BATCH_COUNT - 1)) ] && [ -z "$SPECIFIC_BATCH" ]; then
            echo "Sleeping ${BATCH_SLEEP}s before next batch..."
            sleep "$BATCH_SLEEP"
        fi
    done
    
    echo ""
    echo "✓ Hours stage complete"
fi

# Run minutes stage
if [ "$RUN_MINUTES" = true ]; then
    echo ""
    echo "================================================"
    echo "Running MINUTES stage (active subset)"
    echo "================================================"
    
    python scripts/weekend_history_backfill.py \
        --stage minutes \
        --universe "$UNIVERSE" \
        --top-expiries 5 \
        --strikes-per-side 3 \
        --host "$REMOTE_HOST" \
        --port "$REMOTE_PORT" \
        --client-id "$CLIENT_ID" \
        --historical-per-minute 10 \
        --historical-burst 5 \
        --resume
    
    echo ""
    echo "✓ Minutes stage complete"
fi

echo ""
echo "================================================"
echo "Backfill complete!"
echo "================================================"
echo ""
echo "Output locations:"
echo "  Parquet: data_test/raw/ib/historical_bars_weekend/"
echo "  Summary: state/run_logs/historical_backfill/"
echo ""
echo "Next steps:"
echo "  1. Check summary JSONL for errors:"
echo "     tail state/run_logs/historical_backfill/summary_*.jsonl | jq '.error_message // empty'"
echo ""
echo "  2. Generate rerun universe for failed symbols:"
echo "     python scripts/make_probe_rerun_universe.py \\"
echo "       --input 'state/run_logs/historical_backfill/summary_hours_*.jsonl' \\"
echo "       --output config/universe_history_rerun.csv"
echo ""
echo "  3. Verify data quality:"
echo "     find data_test/raw/ib/historical_bars_weekend -name '*.parquet' | wc -l"
