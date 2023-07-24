'''backtest
start: 2023-04-22 00:00:00
end: 2023-07-23 00:00:00
period: 15m
basePeriod: 5m
exchanges: [{"eid":"Futures_Binance","currency":"ARB_USDT"}]
mode: 1
'''
import time


def trade():
    records = exchange.GetRecords()
    depth = exchange.GetDepth()
    price = float(depth["Bids"][0]["Price"])
    volume_now = float(records[-1]["Volume"])
    volume_last = float(records[-2]["Volume"])
    is_buy_in = volume_now > 10*volume_last
    if is_buy_in:
        orderid = exchange.Buy(price,1)


def main():
    while True:
        trade()
        time.sleep(10)

