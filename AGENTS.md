# AGENTS.md

## Purpose
- This file is the cross-project coordination and archiving rulebook for this repo.
- Each subproject keeps its own execution details in its local AGENTS.md.

## Project boundaries
- option/opt-data: options data pipelines, configs, ops, and docs under option/opt-data/.
- stock/stock-data: stock data pipelines, configs, ops, and docs under stock/stock-data/.

## Planning and task tracking
- Each subproject must maintain its own PLAN.md and TODO.now.md in its subproject root.
- Root-level PLAN.md and TODO.now.md are optional and only for cross-project rollups.
- Do not put subproject-specific tasks in the root TODO unless they affect both projects.

## Documentation placement
- Subproject docs live under its own docs/ folder.
- Repo-wide policies live here or in a top-level docs/ file if created.
- When a rule changes, update the relevant subproject AGENTS.md and any affected docs.

## Config and ops separation
- Do not mix configs between subprojects.
- Ops runbooks and schedules must be maintained per subproject.

## Dependency locking
- Repo-root `requirements.lock` and `requirements-dev.lock` are the canonical lockfiles for shared environments.
- Any subproject `pyproject.toml` change requires regenerating root locks and updating affected docs.

## Change hygiene
- Keep changes scoped to the subproject unless explicitly cross-project.
- If a change affects both, document it in both subproject PLAN.md files and in the root rollup (if used).

## Ownership and review
- Each subproject has its own owner/maintainers and review requirements.
- Cross-project changes require review from both subproject owners.
