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
        """
    ).strip()

    cfg_file = tmp_path / "opt-data.toml"
    cfg_file.write_text(content, encoding="utf-8")

    cfg = load_config(cfg_file)
    assert cfg.ib.host == "127.0.0.2"
    assert cfg.ib.client_id == 102
    assert cfg.paths.raw.name == "raw"
    assert cfg.paths.state.name == "state"

