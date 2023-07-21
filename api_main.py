#!/usr/bin/env python
import sys
import signal
import time
import logging
import json
import enum
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from binance.spot import Spot as Client
from ip_search import get_current_proxy_ip
from threading import Lock,RLock
import matplotlib.pyplot as plt

config_logging(logging, logging.ERROR)

USDCNY = 7.1
INTERVAL = 0

#撤单率
CANCEL_RATE = 0.0

# 买入比例
LOB_THRESHOLD = 0

COIN = "BTCTUSD"

ORDER_AMOUNT = 0.01

profit = 0

position = 0

buy_in_price = 0

#
lock = Lock()

# 监控: orderbook imbalance, tradeflow imbalance , 大单异动，链上数据
# 归一化后做个公式然后打分
obis = []
obis_reverse = []
# 记录买入信号10s后的价格delta
PRICE_CHANGE_AFTER_SIGNAL_DELAY = [0]


def message_handler():
    with lock:
        global buy_in_price, profit, position, ORDER_AMOUNT, obi_amount, obi_sum, obis, SIGNAL
        data_dict = client.depth(symbol=COIN, limit=100)

        bid_1 = float(data_dict["bids"][10][0])
        ask_1 = float(data_dict["asks"][10][0])
        # 监控order book imbalance
        bid_quantity = sum(float(row[1]) for row in data_dict["bids"])
        ask_quantity = sum(float(row[1]) for row in data_dict["asks"])
        obi = bid_quantity / ask_quantity
        obis_reverse.append(1 / obi)
        obis.append(obi)

        # stop loss = 5-1000 * 0.01 = 0.05u-10u
        is_shut_down = (buy_in_price - ask_1) > 1000 or profit < -100
        is_stop_loss = (buy_in_price - ask_1) > 100

        # buy_in signal
        buy_in_signal = obi > 2
        # print(buy_in_signal)
        if position == 0 and buy_in_signal:
            # 下单
            success = do_order(COIN, Trade.BUY.value, 'LIMIT', ORDER_AMOUNT, bid_1)
            if not success:
                logging.debug("下单失败重新下: price:%f amount:%f" % (buy_in_price, ORDER_AMOUNT))
                return
            position = 1
            buy_in_price = bid_1
            print("BID BUY: price:%f amount:%f" % (bid_1, ORDER_AMOUNT))
            time.sleep(INTERVAL)
        elif position == 1 and ask_1 > buy_in_price:
            # 下单止盈
            # print("BID SELL: price:%f amount:%f"% (ask_1, order_amount))
            success = do_order(COIN, Trade.SELL.value, 'LIMIT', ORDER_AMOUNT, ask_1)
            if not success:
                logging.debug("卖出失败重新下: price:%f amount:%f" % (buy_in_price, ORDER_AMOUNT))
                return
            profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
            print("Profit Sell :%f SELL Price:%f" % (profit, ask_1))

            # 记录价格变化
            PRICE_CHANGE_AFTER_SIGNAL_DELAY.append(ask_1 - buy_in_price)
            position = 0
            buy_in_price = 0
            time.sleep(INTERVAL)
        elif position == 1 and is_shut_down:
            # 下单停机
            print("SHUTDOWN ON TRAILING ORDER: buy in:%f price:%f amount:%f！！！！！\n" % (
                buy_in_price, ask_1, ORDER_AMOUNT))
            success = do_order(COIN, Trade.SELL.value, 'LIMIT', ORDER_AMOUNT, ask_1)
            if not success:
                logging.debug("停机失败重新下: price:%f amount:%f" % (buy_in_price, ORDER_AMOUNT))
                return
            profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
            # print("Profit:%f" % profit)
            buy_in_price = 0
            position = 0
            # 停机
            end_time = time.time()
            print("------FINAL PROFIT-------:%f" % profit)
            profit_per_day = (profit / ((end_time - start_time) / 60)) * 24 * 60
            profit_per_month = profit_per_day * 30 * USDCNY
            print("Expected profit/day is %fu, profit/month is %f元" % (profit_per_day, profit_per_month))
            logging.debug("closing ws connection")
            #my_client.stop()
            sys.exit(0)
        elif position == 1 and is_stop_loss:
            # 下单止损
            # print("LOB RATIO IS: %f" % lob_now)
            success = do_order(COIN, Trade.SELL.value, 'LIMIT', ORDER_AMOUNT, ask_1)
            if not success:
                return
            profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
            print("STOP LOSS ON TRAILING ORDER: buy in:%f price:%f amount:%f" % (
                buy_in_price, ask_1, ORDER_AMOUNT))
            print("Profit:%f" % profit)
            buy_in_price = 0
            position = 0
        return


# 下单，没成交就撤单
def do_order(symbol=COIN, side="SELL", _type='LIMIT', quantity=ORDER_AMOUNT, price=None):
    # Post a new order
    params = {
        'symbol': symbol,
        'side': side,
        'type': _type,
        'timeInForce': 'GTC',
        'quantity': quantity,
        'price': price,
        'newOrderRespType': 'ACK',  # ACK
    }
    logging.debug(params)
    try:
        response = client.new_order(**params)
        time.sleep(1)
        response = client.get_order(symbol=symbol, orderId=int(response['orderId']))
        # print(response)
        if response.get('status') == 'PARTIALLY_FILLED':
            residual_quantity = response.get('executedQty')
            return do_order(symbol=symbol, side=side, _type="LIMIT", quantity=quantity-residual_quantity, price=price)
        elif response.get('status') != 'FILLED':
            client.cancel_open_orders(symbol=symbol)
            logging.error("未成交撤单")
            return False
        elif response.get('status') == 'FILLED':
            return True
        return False
    except Exception as e:
        logging.error(params)
        logging.error(e)
        return False
    return False


def handle_signal(signum, frame):
    # 清仓
    global position
    if position == 1:
        success = do_order(COIN, Trade.SELL.value, 'MARKET', ORDER_AMOUNT)
        if not success:
            return
        position = 0
    end_time = time.time()

    # plot_monitor_metrics(obis,"order book imbalance")
    # plot_monitor_metrics(obis_reverse,"oder book  imbalance reverse")
    # 统计PRICE_CHANGE_AFTER_SIGNAL_DELAY
    negative_count = sum(1 for change in PRICE_CHANGE_AFTER_SIGNAL_DELAY if change < 0)
    # 计算小于0的比例
    negative_ratio = negative_count / len(PRICE_CHANGE_AFTER_SIGNAL_DELAY)
    print("\n%ds后亏损的比例为: %.2f%%，交易次数%d\n" %(INTERVAL,negative_ratio*100,len(PRICE_CHANGE_AFTER_SIGNAL_DELAY)))
    print("------FINAL PROFIT-------:%f" % profit)
    profit_per_day = (profit / ((end_time - start_time) / 60)) * 24 * 60
    profit_per_month = profit_per_day * 30 * USDCNY
    print("Expected profit/day is %du, profit/month is %d元" % (profit_per_day, profit_per_month))

    # logging.debug("closing ws connection")
    # my_client.stop()
    #
    # sys.exit()


def plot_monitor_metrics(x,title):
    # 绘制监控图像
    plt.hist(x, bins=20, edgecolor='black')  # bins参数决定直方图的箱数
    plt.xticks(range(20))
    plt.title(title)
    plt.xlabel("OBI")
    plt.ylabel('Frequency')
    # 显示图形
    plt.show()


class Trade(enum.Enum):
    BUY = 'BUY'
    SELL = 'SELL'


if __name__ == '__main__':
    INTERVAL = int(input("Please enter the interval between price changes in seconds (default=3): "))
    # print_profit()
    ip = get_current_proxy_ip()
    print("当前代理 IP:", ip)
    # 注册信号处理程序ctrlz+c
    signal.signal(signal.SIGTSTP, handle_signal)
    # signal.signal(signal.SIGINT, handle_signal)

    # 获取账号:ip_search.py
    client = Client(api_key='Ng4rh2vG90dbfjVXPAzRYPaLpGcWXuSTcxZqmNKtEXyvl1iqwUKeRG6PPqfdUkDZ',
                    api_secret='XxExX9qAXtvKE0aAiP4CiFer8qnF4sxlcoXLNCMFFu7CfTMi95SyOS82I2a5QAVc')
    logging.debug(client.user_asset())
    start_time = time.time()
    # 开始运行
    while True:
        message_handler()
        #time.sleep(INTERVAL)

    #
    # logging.debug("closing ws connection")
    # my_client.stop()
