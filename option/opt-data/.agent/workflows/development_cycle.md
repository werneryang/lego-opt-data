---
description: Standard development workflow for new features or fixes
---
This workflow outlines the steps for implementing new requirements or fixes, ensuring compliance with project standards.

1. **Understand Requirements**
   - Review `TODO.now.md` and `PLAN.md`.
   - If this is a new requirement, update `TODO.now.md` and align with `PLAN.md`.

2. **Design & Documentation**
   - For significant changes, record design decisions in `docs/ADR-xxxx.md` or update `SCOPE.md`.
   - Ensure you understand the "Contract Discovery" rules in `AGENTS.md` if touching IBKR logic.

3. **Development**
   - Implement changes in `src/`.
   - Add or update tests in `tests/`.
   - Follow the module layout: `src/opt_data/ib`, `pipeline`, `storage`, `cli`, `config`.

4. **Quality Assurance**
   - Run the QA workflow to format, lint, and test your code.
   - Command: `/qa` (or `make qa`)

5. **Verification**
   - Before large-scale backfills, use `config/opt-data.test.toml` to test with AAPL/MSFT.
   - Verify data output in `data/raw` and `data/clean`.

6. **Documentation Update**
   - Update `docs/ops-runbook.md` for production changes.
   - Update `docs/dev/` for experimental scripts.

7. **Review & Merge**
   - Ensure CI passes.
   - Verify data integrity (partitions, unique keys, non-nulls).
