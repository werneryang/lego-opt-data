from pathlib import Path

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
