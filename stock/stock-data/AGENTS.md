# AGENTS.md (Stock Data)

## 角色定位
- **智能体**：负责股票行情数据采集、清洗与调度。
- **协同原则**：遵循全局规则 `.agent/rules/global.md`。

## 规范与标准
- **技术栈**：参考 `.agent/rules/tech-stack.md`。
- **数据标准**：参考 `.agent/rules/finance-data-standards.md`。
- **依赖**：使用根目录锁文件，修改 `pyproject.toml` 后运行 `make lock`。

## AI 任务执行优化
- **Claude**: 强化对数据清洗逻辑（拆分、股息调整）的思考验证。
- **Gemini**: 保持对 `stock_data.config` 与 `opt_data.config` 结构一致性的关注。
- **GPT**: 适合执行批量的代码风格统一和文档字符串（Docstrings）补全。
