'''backtest
start: 2023-01-01 00:00:00
end: 2023-07-24 00:00:00
period: 1h
basePeriod: 15m
exchanges: [{"eid":"Binance","currency":"XRP_USDT","stocks":0},{"eid":"Binance","currency":"SOL_USDT","stocks":0},{"eid":"Binance","currency":"SUI_USDT","stocks":0},{"eid":"Binance","currency":"ARB_USDT","stocks":0},{"eid":"Binance","currency":"ADA_USDT","stocks":0},{"eid":"Binance","currency":"LTC_USDT","stocks":0},{"eid":"Binance","currency":"DOGE_USDT","stocks":0},{"eid":"Binance","currency":"AVAX_USDT","stocks":0},{"eid":"Binance","currency":"DYDX_USDT","stocks":0},{"eid":"Binance","currency":"APT_USDT","stocks":0},{"eid":"Binance","currency":"ATOM_USDT","stocks":0},{"eid":"Binance","currency":"LDO_USDT","stocks":0},{"eid":"Binance","currency":"SAND_USDT","stocks":0},{"eid":"Binance","currency":"WAVES_USDT","stocks":0}]
'''

import time

ORDERID = []
ORDERUNIX = []

def init():
    l = len(exchanges)
    ORDERID = [-1] * l
    ORDERUNIX = [-1] * l

def trade(exchange):
    global ORDERID,ORDERUNIX
    records = _C(exchange.GetRecords)
    #Log("k线数量",len(records))
    if len(records) < 10*24:
        #Log("k线数量",len(records))
        Sleep(60*60*1000)
        return
    depth = _C(exchange.GetDepth)
    price = float(depth["Bids"][0]["Price"])

    #
    account = _C(exchange.GetAccount)
    balance = account["Balance"]

    tick_now = records[-1]
    tick_last = records[-2]
    volume_now = float(tick_now["Volume"])
    volume_last = float(tick_last["Volume"])
    #爆量+上涨+破新高
    is_buy_in = volume_now > 8* volume_last and volume_now > max_volume(records[0:-1]) and price > max_price(records[-5*24:-1]) and volume_now > 8 * mean_volume(records[-12:-1]) and price > tick_now["Open"]
    if is_buy_in and ORDERID == -1:
        Sleep(15*60*1000)
        #等会再买,防止冲击了
        tick = _C(exchange.GetTicker)
        price = tick["Sell"]
        orderid= exchange.Buy(price,_N(balance*0.9/price,0))
        #挂单成功
        Sleep(15*60*1000)
        #如果没买入成功，就撤单
        order = _C(exchange.GetOrder,orderid)
        if order["DealAmount"] == 0:
            is_cancled = exchange.CancelOrder(orderid)
            if is_cancled:
                Log(_D(),price,"orderid: ",orderid,"撤单买入成功!!!")
                return
        ORDERID = orderid
        ORDERUNIX = Unix()
        Log(_D(),price,"orderid: ",orderid,"买入成功!!!")
def stopLoss():
    return

#60天最大值
def max_volume(records):
    #max
    return max(r["Volume"] for r in records)

def mean_volume(records):
    #max
    return sum(r["Volume"] for r in records)/len(records)

def max_price(records):
    return max(r["High"] for r in records)

def is_exit_position(exchange):
    global ORDERID,ORDERUNIX
    if ORDERID == -1:
        return
    order = _C(exchange.GetOrder,ORDERID)
    if order and order["Type"] != 0 :
        Log("已经卖出了",order)
        return
    #
    deal_price = float(order["Price"])
    deal_amount = float(order["DealAmount"])
    #
    depth = _C(exchange.GetDepth)
    price = float(depth["Bids"][0]["Price"])

    is_stop_loss = price < 0.90 * deal_price
    #过去2h
    is_exit_profit = int(Unix()) > ORDERUNIX + 2*60*60

    if is_stop_loss or is_exit_profit :
        #Log("卖出ing:",order)
        orderid= exchange.Sell(price,deal_amount)
        Sleep(15*60*1000)
        #没卖出就撤单
        order = _C(exchange.GetOrder,orderid)
        if order["DealAmount"] == 0:
            is_cancled = exchange.CancelOrder(orderid)
            if is_cancled:
                Log("卖出撤单成功")
                return
        #
        ORDERID = -1
        ORDERUNIX = 0
        if is_stop_loss:
            Log("止损卖出成功")
        else:
            Log("止盈卖出成功")


def main():
    while True:
        # Log(len(exchanges))
        # Sleep(60*1000)
        for i in range(len(exchanges)):
            trade(i)
            is_exit_position(i)
            Sleep(60*1000)
