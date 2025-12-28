from pathlib import Path
import pytest

from opt_data.config import load_config


def test_load_config_from_custom_file(tmp_path: Path) -> None:
    content = (
        """
        [ib]
        host = "127.0.0.2"
        port = 7497
        client_id = 102
        market_data_type = 2

        [paths]
        raw = "data/raw"
        clean = "data/clean"
        state = "state"
        contracts_cache = "state/contracts_cache"
        run_logs = "state/run_logs"

        [reference]
        corporate_actions = "config/actions.csv"

        [acquisition]
        mode = "historical"
        duration = "2 D"
        bar_size = "1 hour"
        what_to_show = "MIDPOINT"
        use_rth = false
        max_strikes_per_expiry = 11
        fill_missing_greeks_with_zero = true
        historical_timeout = 45

        [qa]
        slot_coverage_threshold = 0.9
        delayed_ratio_threshold = 0.2
        rollup_fallback_threshold = 0.1
        oi_enrichment_threshold = 0.8
        """
    ).strip()

    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content, encoding="utf-8")

    cfg = load_config(cfg_file)
    assert cfg.ib.host == "127.0.0.2"
    assert cfg.ib.client_id == 102
    assert cfg.paths.raw.name == "raw"
    assert cfg.paths.state.name == "state"
    assert cfg.reference.corporate_actions.name == "actions.csv"
    assert cfg.acquisition.mode == "historical"
    assert cfg.acquisition.duration == "2 D"
    assert cfg.acquisition.max_strikes_per_expiry == 11
    assert cfg.acquisition.fill_missing_greeks_with_zero is True
    assert cfg.acquisition.historical_timeout == 45.0
    assert cfg.cli.snapshot_grace_seconds == 120
    assert cfg.cli.rollup_close_slot == 13
    assert cfg.cli.rollup_fallback_slot == 12
    assert cfg.qa.slot_coverage_threshold == 0.9
    assert cfg.qa.delayed_ratio_threshold == 0.2
    assert cfg.qa.rollup_fallback_threshold == 0.1
    assert cfg.qa.oi_enrichment_threshold == 0.8
    assert cfg.enrichment.fields == ["open_interest"]
    assert cfg.enrichment.oi_duration == "7 D"
    assert cfg.enrichment.oi_use_rth is False


def test_config_validation_rejects_invalid_ib_port(tmp_path: Path) -> None:
    """Test that invalid IB port (outside 1024-65535) is rejected."""
    content = """
        [ib]
        port = 100
        """
    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid IB port: 100"):
        load_config(cfg_file)


def test_config_validation_rejects_invalid_market_data_type(tmp_path: Path) -> None:
    """Test that invalid market_data_type is rejected."""
    content = """
        [ib]
        market_data_type = 10
        """
    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid IB market_data_type"):
        load_config(cfg_file)


def test_config_validation_rejects_invalid_qa_threshold(tmp_path: Path) -> None:
    """Test that QA thresholds outside 0-1 range are rejected."""
    content = """
        [qa]
        slot_coverage_threshold = 1.5
        """
    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match=r"Invalid qa\.slot_coverage_threshold.*1\.5"):
        load_config(cfg_file)


def test_config_validation_rejects_negative_rate_limit(tmp_path: Path) -> None:
    """Test that negative rate limits are rejected."""
    content = """
        [rate_limits.snapshot]
        per_minute = -10
        """
    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match=r"Invalid rate_limits\.snapshot\.per_minute.*-10"):
        load_config(cfg_file)


def test_config_validation_rejects_invalid_moneyness(tmp_path: Path) -> None:
    """Test that moneyness_pct outside valid range is rejected."""
    content = """
        [filters]
        moneyness_pct = 1.5
        """
    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match=r"Invalid filters\.moneyness_pct.*1\.5"):
        load_config(cfg_file)


def test_config_validation_rejects_invalid_acquisition_mode(tmp_path: Path) -> None:
    """Test that invalid acquisition mode is rejected."""
    content = """
        [acquisition]
        mode = "invalid_mode"
        """
    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match=r"Invalid acquisition\.mode: invalid_mode.*Valid modes"):
        load_config(cfg_file)


def test_config_validation_rejects_invalid_log_level(tmp_path: Path) -> None:
    """Test that invalid logging level is rejected."""
    content = """
        [logging]
        level = "INVALID"
        """
    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match=r"Invalid logging\.level: INVALID"):
        load_config(cfg_file)


def test_config_validation_rejects_invalid_compaction_size(tmp_path: Path) -> None:
    """Test that max_file_size_mb < min_file_size_mb is rejected."""
    content = """
        [compaction]
        min_file_size_mb = 256
        max_file_size_mb = 128
        """
    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content.strip(), encoding="utf-8")

    with pytest.raises(ValueError, match=r"compaction\.max_file_size_mb.*must be.*min"):
        load_config(cfg_file)
