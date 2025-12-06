《基于 ib_insync 的 TWS 期权链数据拉取正式方案（Production Version）》
1. 总览（Executive Summary）
Interactive Brokers 原生 API（ibapi）过于底层、不利于大规模期权链抓取。
ib_insync 引入同步/异步封装，使得：
批量合约管理更简洁
快照行情拉取更高效
异步管线更适合大规模期权链
避免合约详情、回调、消息循环等复杂实现
本方案目标是：
针对四大时间段（盘前、盘中、盘后、周末），提供最优数据拉取组合方案
并给出
函数调用格式、参数选择、限制说明、避免使用的调用模式、扩展组合场景。
2. 核心函数（完整调用格式 + 参数说明）
注意：下列不是代码，而是“调用格式说明”。
2.1 获取期权链结构（行权价 + 到期日）
函数格式
ib.reqSecDefOptParams(
    underlyingSymbol,
    futFopExchange,
    underlyingSecType,
    underlyingConId
)
关键参数意义
underlyingSymbol：如 "SPY"
futFopExchange：股票期权永远为空字符串 ""
underlyingSecType：股票 → "STK"
underlyingConId：标的通过 qualifyContracts 后的 conId
返回值
包含：
tradingClass
exchange
expirations（到期日）
strikes（行权价）
适用场景
盘前/盘后/周末统一使用
第一层合约结构来源
禁止用法（重要）
❌ 禁止循环调用 reqContractDetails 获取链条
（慢 × 冗余 × 高负荷）
2.2 批量合约正规化（获取 conId 等）
函数格式
ib.qualifyContracts(contract1, contract2, ...)
目的
让 IB 填充：
conId
tradingClass
multiplier
正规化 exchange
适用场景
生成完整链条库
合约增量更新
2.3 快照行情（Snapshot）
函数格式
ib.reqMktData(
    contract,
    genericTickList="",
    snapshot=True,
    regulatorySnapshot=False
)
参数说明
snapshot=True：关键，用于批量抓取
genericTickList：OI/IV/Delta 等需要时填写（如下）
regulatorySnapshot=False：永远保持 False
常用 Tick 组合
数据	Tick Code
未平仓量 OI	100, 101, 104 或 option-specific tick（27/28）
隐含波动率	106
Delta/Gamma/Vega/Theta	104
（Tick 类型依 IB 行情权限不同而变化）
2.4 批量快照（更推荐的方式）
函数格式
ib.reqTickers(contract1, contract2, ...)
优势
自动并发
自动等待所有返回
自动合并 ticker 对象
注意
仍然属于 snapshot，本质上依赖 snapshot=True 内部实现（不消耗 streaming 线路）。
2.5 Streaming 实时行情（仅少量重点合约）
函数格式
ib.reqMktData(
    contract,
    genericTickList="",
    snapshot=False
)
限制
100 条实时订阅限制（可购买更多但成本高）
不适合期权链
禁止项
❌ 禁止为几十至上千个合约使用 streaming（reqMktData snapshot=False）
2.6 Scanner（全市场筛选）
函数格式
ib.reqScannerSubscription(
    scannerSubscription,
    scannerFilterOptions=None,
    scannerSubscriptionOptions=None
)
适用场景
周末全市场“活跃期权”筛选
盘后市场扫描（例如日内成交量排名）
2.7 历史数据（日线/分钟）
函数格式
ib.reqHistoricalData(
    contract,
    endDateTime,
    durationStr,
    barSizeSetting,
    whatToShow,
    useRTH,
    formatDate,
    keepUpToDate=False
)
适用场景
盘后获取官方收盘价格
周末统计历史 IV、HV、成交量
3. 四大时间段的最终方案（最佳组合）
下面为生产环境推荐方案（强建议采用）。
3.1 盘前（Pre-Market）
🎯 目标
OI（前一日清算后）
最新链条结构（增量）
非实时的 snapshot 行情
✅ 推荐调用组合
Market Data Type = 2 （Frozen / 结算后冻结行情）
任务	使用函数	参数
更新链条结构	reqSecDefOptParams	全部默认
新链条正规化	qualifyContracts	合约列表
更新 OI	reqMktData	snapshot=True, tickList="27,28"
更新全部链 snapshot	reqTickers	所有合约
❌ 避免
streaming（盘前没有连续行情）
依赖盘前价格做交易信号（不稳定）
3.2 盘中（Market Open）
🎯 目标
每 30 min 获取全链 snapshot
对主力合约进行实时流订阅（非常少量）
动态合约增量更新（标的暴涨后新增 strike）
✅ 推荐组合
Market Data Type = 1（Real-Time）
任务	方法	参数
主力合约流行情	reqMktData	snapshot=False
大规模链行情（1000+）	reqTickers	snapshot 自动
OI（不需频繁）	reqMktData snapshot=True	tickList="27,28"
链条变动	reqSecDefOptParams	每 2 小时或价差阈值触发
❌ 避免
reqTickers + streaming 混用同一批合约
过频繁调用 reqContractDetails
3.3 盘后（After-Market）
🎯 目标
收盘价（Frozen）
链条更新
500 个标的 × 各自期权链的批量数据
✅ 推荐组合
Market Data Type = 2（Frozen 数据）
任务	方法	参数
500 标的链条结构	reqSecDefOptParams	用合约缓存增量更新
正规化	qualifyContracts	全链合约
收盘数据	reqTickers	snapshot（Frozen）
昨收价	reqHistoricalData	whatToShow=TRADES / MIDPOINT
❌ 避免
streaming（无意义）
逐合约 snapshot（效率差）
3.4 周末（Weekend）
🎯 目标
全市场扫描
合约库维护（新增/到期）
大规模数据统计（如活跃度）
✅ 推荐组合
Market Data Type = 2（Frozen）
任务	方法	参数
全市场活跃期权扫描	reqScannerSubscription	scanCode="HIGH_OPT_VOLUME"
全市场链条更新	reqSecDefOptParams	对标的池循环
新增合约正规化	qualifyContracts	仅新增合约
全市场快照	reqTickers	返回周五收盘价
❌ 避免
OI（周末不更新）
streaming（无行情）
4. 高并发快照架构设计（正式版）
4.1 原则
snapshot 和 streaming 分离
snapshot 批次控制
异步 + 信号量限流
合约库缓存（避免重复请求）
4.2 架构流程
[合约列表] → [按 200–300 分组] → [组内批量调用 reqTickers] 
      → [ticker 对象归集] → [写入数据库] → [下一组]
推荐参数
每批合约 <= 300
两批间 sleep(0.5s)
每秒 snapshot 请求不超过 50–100（安全）
5. 合约库构建（正式流程图）
(1) 获取标的列表
      ↓
(2) 标的合约 qualifyContracts
      ↓
(3) reqSecDefOptParams 获取期权链结构
      ↓
(4) 生成所有 Option 合约对象（C/P × Strike × Exp）
      ↓
(5) qualifyContracts 批量正规化
      ↓
(6) 写入本地库（SQLite / PostgreSQL）
      ↓
(7) 增量更新：
    - 新 expiry?
    - 新 strike?
    - 合约到期清理？
6. 数据缓存与增量更新（正式方案）
6.1 缓存内容
conId（核心）
multiplier
tradingClass
exchange
lastTradeDate
localSymbol
6.2 增量更新规则
每日下午收盘：更新到期日
价格大变动：检查 strike 变化
每周末：合约库整体刷新
到期日后：清除已到期合约
7. 应避免的函数调用与参数（正式禁用表）
函数	禁用原因
reqContractDetails（大量循环）	非常慢、易超限、无法用于链条
reqMktData snapshot=False（大批量）	Streaming 限制，最多 100 条
reqTickers（在市场关闭时）	可能返回无效数据（无快照）
reqHistoricalData keepUpToDate=True	非必要且严重占用资源
8. 其他组合方案（扩展场景 + 使用案例）
8.1 “微盘中扫描”组合
适用：每 5 分钟更新 300 个链条
组合：
snapshot：reqTickers
scanner：reqScannerSubscription
主力 streaming：reqMktData
8.2 “期权波动率地图”组合
适用：创建全市场波动率热力图
组合：
链条：reqSecDefOptParams
snapshot：reqTickers(genericTickList="106")
历史：reqHistoricalData(whatToShow=OPTION_IMPLIED_VOLATILITY)
8.3 “事件前集中加载”组合
适用：财报前、CPI 前
组合：
snapshot（多批次）
scanner（寻找高 IV 合约）
历史（获取过去三次事件的反应）
8.4 “跨标的套利链对链比较”组合
适用：SPY / IVV / VOO 比价
组合：
多标的合约库
snapshot（两组同时拉取）
自定义价差计算器
📌 最终说明
本正式文档已经满足：
完整的 ib_insync 调用格式
参数选择理由
四大时间段最优方案
禁止使用的函数与参数
扩展组合场景
架构、流程、增量更新等全部工程化内容
如你需要，我还能提供：
✔ 架构图（图形化）
✔ 第一期 MVP 版本的“模块设计图”
✔ 性能测试标准（像 QPS / IB 限流点）