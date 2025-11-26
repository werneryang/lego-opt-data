#!/usr/bin/env python3
"""
Manual error scenario testing script.

This script helps manually test various error scenarios in a real environment.
It's designed to be run against a test IB Gateway/TWS connection.

Usage:
    python scripts/test_error_scenarios.py --scenario subscription_failed
    python scripts/test_error_scenarios.py --scenario timeout
    python scripts/test_error_scenarios.py --scenario all

Scenarios:
    - subscription_failed: Test with invalid contract
    - timeout: Test with very short timeout
    - permission_denied: Test with contract requiring special permissions
    - partial_failure: Test with mix of valid and invalid contracts
    - all: Run all scenarios
"""

import argparse
import json
import logging
from datetime import date
from pathlib import Path

from opt_data.config import load_config
from opt_data.ib.session import IBSession
from opt_data.ib.snapshot import collect_option_snapshots

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_subscription_failed(ib, cfg):
    """Test scenario: Invalid contract that should fail subscription."""
    logger.info("=" * 60)
    logger.info("Testing: SUBSCRIPTION_FAILED scenario")
    logger.info("=" * 60)
    
    # Create an intentionally invalid contract
    invalid_contracts = [{
        "symbol": "INVALID_SYMBOL_XYZ",
        "strike": 999999.0,
        "right": "C",
        "expiry": "19900101",  # Expired date
        "exchange": "SMART",
        "currency": "USD",
        "conid": None,  # No conId, forcing fallback creation
    }]
    
    try:
        results = collect_option_snapshots(
            ib,
            invalid_contracts,
            timeout=5.0,
            require_greeks=False,
        )
        
        logger.info(f"Results count: {len(results)}")
        for result in results:
            logger.info(f"Result: {json.dumps(result, indent=2, default=str)}")
            
            # Verify error fields
            if result.get("snapshot_error"):
                logger.info(f"✓ Error correctly flagged")
                logger.info(f"  Error type: {result.get('error_type')}")
                logger.info(f"  Error message: {result.get('error_message')}")
            else:
                logger.warning(f"✗ Expected snapshot_error=True but got {result.get('snapshot_error')}")
                
    except Exception as e:
        logger.error(f"Exception raised: {type(e).__name__}: {e}")
        logger.info("This is acceptable if it's a RuntimeError from collect_option_snapshots")


def test_timeout(ib, cfg):
    """Test scenario: Very short timeout causing data not ready."""
    logger.info("=" * 60)
    logger.info("Testing: TIMEOUT scenario")
    logger.info("=" * 60)
    
    # Use a real contract but with very short timeout
    contracts = [{
        "symbol": "AAPL",
        "strike": 150.0,
        "right": "C",
        "expiry": "20251231",
        "exchange": "SMART",
        "currency": "USD",
    }]
    
    try:
        results = collect_option_snapshots(
            ib,
            contracts,
            timeout=0.1,  # Very short timeout - 100ms
            poll_interval=0.05,
            require_greeks=True,  # Require greeks to increase chance of timeout
        )
        
        logger.info(f"Results count: {len(results)}")
        for result in results:
            if result.get("snapshot_timed_out"):
                logger.info(f"✓ Timeout correctly detected")
                logger.info(f"  Price ready: {result.get('price_ready')}")
                logger.info(f"  Greeks ready: {result.get('greeks_ready')}")
            elif result.get("snapshot_error"):
                logger.info(f"✓ Error flagged (might be timeout or other error)")
                logger.info(f"  Error type: {result.get('error_type')}")
            else:
                logger.info(f"Data was ready within timeout - try shorter timeout")
                
    except Exception as e:
        logger.error(f"Exception raised: {type(e).__name__}: {e}")


def test_partial_failure(ib, cfg):
    """Test scenario: Mix of valid and invalid contracts."""
    logger.info("=" * 60)
    logger.info("Testing: PARTIAL_FAILURE scenario")
    logger.info("=" * 60)
    
    mix_contracts = [
        # Valid contract
        {
            "symbol": "AAPL",
            "strike": 150.0,
            "right": "C",
            "expiry": "20251231",
            "exchange": "SMART",
            "currency": "USD",
        },
        # Invalid contract
        {
            "symbol": "INVALID_XYZ",
            "strike": 999999.0,
            "right": "C",
            "expiry": "19900101",
            "exchange": "SMART",
            "currency": "USD",
        },
        # Another valid contract
        {
            "symbol": "MSFT",
            "strike": 400.0,
            "right": "P",
            "expiry": "20251231",
            "exchange": "SMART",
            "currency": "USD",
        },
    ]
    
    try:
        results = collect_option_snapshots(
            ib,
            mix_contracts,
            timeout=5.0,
            require_greeks=False,
        )
        
        logger.info(f"Results count: {len(results)}")
        
        success_count = sum(1 for r in results if not r.get("snapshot_error"))
        error_count = sum(1 for r in results if r.get("snapshot_error"))
        
        logger.info(f"✓ Successful contracts: {success_count}")
        logger.info(f"✓ Failed contracts: {error_count}")
        
        for i, result in enumerate(results):
            symbol = result.get("symbol")
            if result.get("snapshot_error"):
                logger.info(f"  [{i}] {symbol}: ERROR - {result.get('error_type')}")
            else:
                logger.info(f"  [{i}] {symbol}: SUCCESS - bid={result.get('bid')}, ask={result.get('ask')}")
                
    except Exception as e:
        logger.error(f"Exception raised: {type(e).__name__}: {e}")


def main():
    parser = argparse.ArgumentParser(description="Test error scenarios in snapshot collection")
    parser.add_argument(
        "--scenario",
        choices=["subscription_failed", "timeout", "partial_failure", "all"],
        default="all",
        help="Which error scenario to test"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/opt-data.test.toml",
        help="Path to config file"
    )
    
    args = parser.parse_args()
    
    # Load config
    cfg = load_config(Path(args.config))
    logger.info(f"Loaded config from {args.config}")
    
    # Connect to IB
    session = IBSession(
        host=cfg.ib.host,
        port=cfg.ib.port,
        client_id=cfg.ib.client_id,
        market_data_type=cfg.ib.market_data_type
    )
    
    with session:
        ib = session.ensure_connected()
        logger.info(f"Connected to IB Gateway at {cfg.ib.host}:{cfg.ib.port}")
        
        scenarios = {
            "subscription_failed": test_subscription_failed,
            "timeout": test_timeout,
            "partial_failure": test_partial_failure,
        }
        
        if args.scenario == "all":
            for name, test_func in scenarios.items():
                try:
                    test_func(ib, cfg)
                except Exception as e:
                    logger.error(f"Scenario {name} raised exception: {e}")
                logger.info("")  # Empty line between scenarios
        else:
            test_func = scenarios[args.scenario]
            test_func(ib, cfg)
    
    logger.info("=" * 60)
    logger.info("Error scenario testing completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
