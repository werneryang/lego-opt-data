#!/bin/bash
# Test OI enrichment with optimized snapshot mode

set -e

echo "=== OI Enrichment Test (Snapshot Mode) ==="
echo ""
echo "Prerequisites:"
echo "  - IB Gateway/TWS must be running"
echo "  - Daily data must exist for the target date"
echo ""

# Configuration
SYMBOL="QQQ"
DATE="2025-11-27"

echo "Testing enrichment for $SYMBOL on $DATE..."
echo ""

# Run enrichment
echo "Command: python -m opt_data.cli enrichment --date $DATE --symbols $SYMBOL --fields open_interest"
python -m opt_data.cli enrichment --date $DATE --symbols $SYMBOL --fields open_interest

echo ""
echo "=== Checking Results ==="

# Check if OI was populated
python3 << EOF
import pandas as pd
from pathlib import Path

# Find the enrichment file
pattern = f"data/clean/ib/chain/view=daily_clean/date=$DATE/underlying=$SYMBOL/**/*.parquet"
files = list(Path(".").glob(pattern))

if not files:
    print(f"❌ No data file found for $SYMBOL on $DATE")
    exit(1)

df = pd.read_parquet(files[0])
oi_count = df['open_interest'].notna().sum()
total = len(df)

print(f"📊 Results:")
print(f"  Total contracts: {total}")
print(f"  OI populated: {oi_count}/{total} ({oi_count/total*100:.1f}%)")

if oi_count > 0:
    print(f"\n✅ SUCCESS: OI enrichment worked!")
    print(f"\nSample OI values:")
    sample = df[df['open_interest'].notna()][['symbol','strike','right','open_interest']].head(5)
    print(sample.to_string(index=False))
else:
    print(f"\n❌ FAILED: No OI data retrieved")
    print(f"\nPossible reasons:")
    print(f"  - snapshot=True may not work for tick 101")
    print(f"  - Account permissions")
    print(f"  - Data not available yet (need T+1)")

EOF
