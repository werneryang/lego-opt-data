from ib_insync import IB, Index, Option  # type: ignore
import asyncio

ib = IB()


async def get_spx_chain_in_3_seconds():
    await ib.connectAsync("127.0.0.1", 7496, clientId=1)
    ib.reqMarketDataType(4)

    spx = Index("SPX", "CBOE")
    await ib.qualifyContractsAsync(spx)

    chains = await ib.reqSecDefOptParamsAsync(spx.symbol, "", spx.secType, spx.conId)
    chain = next(c for c in chains if c.exchange == "SMART")

    # 只取最近12个到期日（含0DTE、周五、月）
    expirations = sorted(chain.expirations)[:12]

    spot = spx.marketPrice()
    strikes = [s for s in chain.strikes if spot * 0.7 < s < spot * 1.3 and s % 5 == 0]

    contracts = [
        Option("SPX", exp, s, r, "SMART") for r in "CP" for exp in expirations for s in strikes
    ]

    contracts = await ib.qualifyContractsAsync(*contracts)

    # 批量订阅（30秒全到希腊）
    await asyncio.gather(*(ib.reqMktDataAsync(c, "", False, False) for c in contracts))
    await asyncio.sleep(3)

    print(f"发现+订阅完成！共 {len(contracts)} 个合约")
    for c in contracts[:5]:
        t = ib.ticker(c)
        print(f"{c.localSymbol} IV={t.impliedVolatility * 100:5.2f}% Delta={t.delta:+.3f}")


# 运行
asyncio.run(get_spx_chain_in_3_seconds())
