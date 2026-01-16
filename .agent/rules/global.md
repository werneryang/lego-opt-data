# Global AI Collaboration Rules

## 1. Project Context & Philosophy
- **Modular Data Pipelines**: This repository is a collection of finance data pipelines (`option`, `stock`, etc.). Each should be treated as an independent but interoperable module.
- **Source of Truth**: 
    - Task tracking: `TODO.now.md` and `PLAN.md` in each subproject.
    - Technical specs: `.agent/rules/*.md` and `docs/`.
- **Communication**: Always assume a collaborative "Pair Programmer" role. Proactively flag risks (e.g., API limits, data quality).

## 2. Model-Specific Optimization
- **Claude (Logic & Structure)**: 
    - Use `<thinking>` blocks to reason through complex financial logic or asynchronous code before implementation.
    - Leverage XML-like tags for strict adherence to data schemas.
- **Gemini (Context & Breadth)**:
    - Perform "Whole Project Scans" when modifying shared utilities or config structures.
    - Use the long context window to cross-reference `docs/ADR` with current implementation.
- **GPT (Instruction Adherence & Refactoring)**:
    - **GPT-4o**: Focus on strict instruction following and code DRYness. Proactively suggest abstractions for shared logic between stock and option projects.
    - **OpenAI o1**: Provide clear constraints (e.g., "Must use ib_insync") and allow it to handle complex edge cases in data cleaning logic.

## 3. General Development Standards
- **Python**: 3.11+, strict type hinting, `from __future__ import annotations`.
- **Documentation**: If a function changes behavior, update the docstring AND the corresponding `docs/` or `.agent/rules` file (Refer to `syncing.md`).
- **Safety**: Never hardcode credentials. Use `.env` or system environment variables.
- **Testing**: Before declaring a task "Done", ensure formatting (`ruff`), linting, and tests (`pytest`) pass.

## 4. Cross-Project Dependencies
- Root `requirements.lock` and `requirements-dev.lock` are the master dependency lists.
- Any change to a subproject's `pyproject.toml` requires a `make lock` at the root.
