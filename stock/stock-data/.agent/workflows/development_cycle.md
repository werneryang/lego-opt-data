---
description: Standard development workflow for new features or fixes (Stock Data)
---
This workflow outlines the steps for implementing new requirements or fixes in stock-data.

1. **Understand Requirements**
   - Review `TODO.now.md` and `PLAN.md` in `stock/stock-data/`.

2. **Development**
   - Implement changes in `src/stock_data/`.
   - Update tests in `tests/`.

3. **QA**
   - Run `pytest` and `ruff check`.

4. **Verification**
   - Validate with a single symbol (e.g., AAPL) before full runs.
   - Check Parquet output in `data/raw` and `data/clean`.
