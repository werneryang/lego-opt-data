# 结构迁移最小停机手册

> 适用范围：个人开发与生产运维。目标是完成仓库结构升级（多包/多资产），数据目录保持原位，通过配置指向旧路径，避免停机。

## 目标结构（示例）
```
legosmos/
  option/
    opt-data/
    opt-analysis/
  stock/
    stock-data/
    stock-analysis/
  shared/
  configs/
  data_lake/   # 占位或 gitignored
  docs/
```

## 总体策略
- 数据目录不动：配置仍在 `config/`，先保持指向当前数据根（旧路径）；`configs/` 为目标入口，完成迁移后仅需改前缀路径。
- `data_lake/` 仅作占位或 `.gitignore`。
- 迁移顺序：先 GitHub 仓库，再开发机，最后生产机。
- 兼容与回滚：迁移窗口内保留旧入口脚本/命令，必要时可快速回退到旧结构。

## GitHub 仓库（必须同步）
- MUST：创建目标目录结构（`option/opt-data`、`option/opt-analysis`、`stock/stock-data`、`stock/stock-analysis`、`shared`、`configs`）。
- MUST：更新各包 `pyproject.toml`、入口命令、导入路径与 README；确保多包可独立 `pip install -e`。
- MUST：准备 `configs/` 入口（目标）；过渡期间继续使用 `config/`，确保配置指向旧数据目录。
- MUST：更新 CI/Makefile/脚本路径与文档链接；确保 `make fmt lint test` 与调度脚本可用。
- SHOULD：保留旧命令别名/兼容脚本（短期），减少生产切换风险。
- CAN：添加 `data_lake/` 占位目录与 `.gitignore` 规则（不做物理迁移）。

## 开发机（必须同步）
- MUST：拉取新结构代码，单一虚拟环境内执行多包 `pip install -e`。
- MUST：本地配置继续指向旧数据路径（例如 `config/opt-data.local.toml`）。
- MUST：跑最小冒烟（AAPL/MSFT snapshot/rollup 任一链路）确认写入正常。
- SHOULD：更新 IDE 路径、脚本入口与快捷命令。

### 命令清单（示例）
> 以单一 venv + 多包可编辑安装为例，命令从仓库根目录执行；涉及配置与 CLI 时切换到 `option/opt-data`。

```bash
cd /ABS/PATH/TO/legosmos
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e option/opt-data -e option/opt-analysis -e shared
# 可选：如果已创建 stock 包
pip install -e stock/stock-data -e stock/stock-analysis
```

```bash
# 进入 opt-data 子项目目录
cd /ABS/PATH/TO/legosmos/option/opt-data
# 配置准备（当前仍在 config/）
cp config/opt-data.toml config/opt-data.local.toml
cp config/opt-data.toml config/opt-data.test.toml
```

```bash
# 最小冒烟（示例）
python -m opt_data.cli schedule --simulate --config config/opt-data.test.toml --symbols AAPL,MSFT
# 或单次快照
python -m opt_data.cli snapshot --date today --slot 09:30 --symbols AAPL --config config/opt-data.test.toml
```

## 生产机（必须同步）
- MUST：部署新结构代码与配置，保持数据路径不变。
- MUST：更新调度器/launchd/systemd 指向新入口命令与工作目录。
- MUST：执行一次轻量闭环验证（snapshot → rollup 或 close-snapshot → rollup），确认分区与日志正常。
- SHOULD：记录迁移结果到运行日志或运维文档变更记录。

### 命令清单（示例）
> 生产机建议使用与开发机一致的 venv，配置仍指向旧数据路径。

```bash
cd /ABS/PATH/TO/legosmos
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e option/opt-data -e option/opt-analysis -e shared
```

```bash
# 进入 opt-data 子项目目录
cd /ABS/PATH/TO/legosmos/option/opt-data
# 轻量验证（安全窗口执行，贴近日常：close-snapshot → rollup）
export IB_MARKET_DATA_TYPE=2
python -m opt_data.cli close-snapshot --date today --config config/opt-data.local.toml
python -m opt_data.cli rollup --date today --config config/opt-data.local.toml
python -m opt_data.cli selfcheck --date today --config config/opt-data.local.toml --log-max-total 1
python -m opt_data.cli logscan --date today --config config/opt-data.local.toml --max-total 1
```

## iMac 生产迁移清单（本机）

前置约定：
- 仓库根路径：`/users/michaely/projects/legosmos`
- data_lake 根路径：`/users/michaely/projects/legosmos/data_lake`（gitignored；如迁移到外置盘请改为绝对路径）
- Python/venv：与开发机一致
- IB Gateway：本机 `127.0.0.1:4001`
- 调度方式：launchd
- 保留远程检查脚本：`scripts/ops/check_prod_schedule_remote.sh`

步骤（最小可运行路径）：
1. 同步代码与 venv（按本手册“生产机”章节）。
2. 生成本机生产配置：确认 `config/opt-data.local.toml` 已存在（不存在则 `cp config/opt-data.toml config/opt-data.local.toml`），并将 `paths.*` 改为绝对路径（示例按仓库根）：

```toml
[paths]
raw = "/users/michaely/projects/legosmos/option/opt-data/data/raw/ib/chain"
clean = "/users/michaely/projects/legosmos/option/opt-data/data/clean/ib/chain"
state = "/users/michaely/projects/legosmos/option/opt-data/state"
contracts_cache = "/users/michaely/projects/legosmos/option/opt-data/state/contracts_cache"
run_logs = "/users/michaely/projects/legosmos/option/opt-data/state/run_logs"
```

> 如需统一到 data_lake，可将 `raw/clean` 改为 `.../data_lake/option/raw/ib/chain` 与 `.../data_lake/option/clean/ib/chain`。

3. launchd 配置：复制 `docs/ops/launchd/com.legosmos.opt-data.timer.plist` 到 `~/Library/LaunchAgents/`，把仓库路径替换为 `/users/michaely/projects/legosmos`，并确保 `TZ=America/New_York`。
4. 启用 launchd（按 `docs/ops/ops-runbook.md` 的 macOS launchd 小节），并在安全窗口完成一次轻量验证（close-snapshot → rollup → selfcheck/logscan）。
5. 远程检查（从开发机执行）：

```bash
scripts/ops/check_prod_schedule_remote.sh --host <imac_host> --repo /users/michaely/projects/legosmos/option/opt-data
```

## 验证与回滚（必须同步）
- MUST：验证 `state/run_logs/`、分区完整性、`selfcheck/logscan` 结果为 PASS。
- MUST：保留旧结构的 tag/备份配置；若失败，回滚到旧入口并恢复原配置。

## 旧入口 alias（建议保留 1–2 周）
> 目的：旧命令/脚本不失效，迁移窗口内可随时回退。

```bash
# shell alias（示例）
export LEGOSMOS_ROOT="/ABS/PATH/TO/legosmos"
alias opt-data-schedule='(cd "$LEGOSMOS_ROOT/option/opt-data" && python -m opt_data.cli schedule --live --config config/opt-data.local.toml)'
alias opt-data-close='(cd "$LEGOSMOS_ROOT/option/opt-data" && python -m opt_data.cli close-snapshot --date today --config config/opt-data.local.toml)'
```

```bash
# 旧脚本转发（示例）
# 假设旧脚本仍在 scripts/launchd/opt-data-daily.sh
cat > scripts/launchd/opt-data-daily.sh <<'EOF'
#!/usr/bin/env bash
exec "$LEGOSMOS_ROOT/option/opt-data/scripts/launchd/opt-data-daily.sh" "$@"
EOF
chmod +x scripts/launchd/opt-data-daily.sh
```

## 数据迁移（可延后）
- CAN：选择低峰窗口，将旧数据复制/同步至统一 `data_lake`；切换配置后再做完整 QA。
- CAN：若使用软链接或挂载点，确保权限与路径对齐并在配置中显式记录。

## 完成标准
- 生产调度可运行，核心任务无异常中断。
- 数据落地路径符合配置，未产生重复/混杂分区。
- `selfcheck/logscan` 结果为 PASS。
