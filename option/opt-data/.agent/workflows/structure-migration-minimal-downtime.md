---
description: Minimal-downtime repo structure migration (code/config first, data path unchanged)
---
This workflow migrates repo structure without moving data directories.
Source guide: `docs/migration-minimal-downtime.md`.

1. GitHub repo
- Create new package layout and update `pyproject.toml`/imports/entrypoints.
- Keep config in `config/` during transition; later move to `configs/` without changing data paths.
- Update CI/scripts/docs links; keep short-term compatibility alias if needed.

2. Dev machine
- `pip install -e` each package in one venv.
- Keep `config/opt-data.local.toml` pointing at old data path.
- Run minimal smoke (snapshot/rollup or schedule --simulate) from `option/opt-data`.

3. Prod machine
- Deploy new code/config, update scheduler/launchd paths.
- Run close-snapshot → rollup validation and check `selfcheck/logscan`.

Notes:
- Data migration is optional and can be done later; update config after verifying.
