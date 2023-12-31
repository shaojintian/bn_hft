#!/usr/bin/env python
import sys
import signal
import time
import logging
import json
import enum
from docs.binance.lib.utils import config_logging
from docs.binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from docs.binance.spot import Spot as Client
from ip_search import get_current_proxy_ip
from threading import Lock
import matplotlib.pyplot as plt


config_logging(logging, logging.ERROR)

# 买入比例
LOB_THRESHOLD = 0

COIN = "BTCTUSD"

ORDER_AMOUNT = 0.01

profit = 0

position = 0

buy_in_price = 0


#
lock = Lock()

#监控: orderflow imbalance, tradeflow imbalance , 大单异动，链上数据
#归一化后做个公式然后打分
obis = []

#记录买入信号10s后的价格delta
SIGNAL = False
PRICE_CHANGE_AFTER_SIGNAL_DELAY = []


def message_handler(_, message):
    with lock:
        global buy_in_price, profit, position, ORDER_AMOUNT,obi_amount,obi_sum,obis
        data_dict = json.loads(message)

        bid_1 = float(data_dict["bids"][0][0])
        ask_1 = float(data_dict["asks"][0][0])

        #监控order book imbalance
        bid_quantity = sum(float(row[1]) for row in data_dict["bids"])
        ask_quantity = sum(float(row[1]) for row in data_dict["asks"])
        obi = bid_quantity/ask_quantity
        obis.append(obi)

        # stop loss = 5-1000 * 0.01 = 0.05u-10u
        is_shut_down = (buy_in_price - ask_1) > 1000
        is_stop_loss = (buy_in_price - ask_1) > 5

        if position == 0:
            buy_in_price = bid_1
            # float(data_dict["bids"][0][1])
            # 下单
            do_order(COIN, Trade.BUY.value, 'LIMIT', ORDER_AMOUNT, buy_in_price)
            # print("BID BUY: price:%f amount:%f"% (buy_in_price, order_amount))
            #
            position = 1
        elif position == 1 and ask_1 > buy_in_price:
            # 下单止盈
            # print("BID SELL: price:%f amount:%f"% (ask_1, order_amount))
            do_order(COIN, Trade.SELL.value, 'LIMIT', ORDER_AMOUNT, ask_1)
            profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
            print("Profit:%f OBI:%f" % (profit,obi))
            #
            buy_in_price = 0
            position = 0
        elif position == 1 and is_shut_down:
            # 下单停机
            print("SHUTDOWN ON TRAILING ORDER: buy in:%f price:%f amount:%f！！！！！\n" % (
                buy_in_price, ask_1, ORDER_AMOUNT))
            do_order(COIN, Trade.SELL.value, 'LIMIT', ORDER_AMOUNT, ask_1)
            profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
            # print("Profit:%f" % profit)
            buy_in_price = 0
            position = 0
            # 停机
            end_time = time.time()
            print("------FINAL PROFIT-------:%f" % profit)
            print("Expected profit per day is %f" % ((profit / ((end_time - start_time) / 60)) * 24 * 60))
            logging.debug("closing ws connection")
            my_client.stop()
        elif position == 1 and is_stop_loss:
            # 下单止损
            # print("STOP LOSS ON TRAILING ORDER: buy in:%f price:%f amount:%f！！！！！\n" % (buy_in_price, ask_1, ORDER_AMOUNT))
            # print("LOB RATIO IS: %f" % lob_now)
            do_order(COIN, Trade.SELL.value, 'LIMIT', ORDER_AMOUNT, ask_1)
            profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
            # print("Profit:%f" % profit)
            buy_in_price = 0
            position = 0


# fuck this fuction
def do_order(symbol=COIN, side="SELL", _type='LIMIT', quantity=ORDER_AMOUNT, price=None):
    return
    # # Post a new order
    # params = {
    #     'symbol': symbol,
    #     'side': side,
    #     'type': _type,
    #     'timeInForce': 'GTC',
    #     'quantity': quantity,
    #     'price': price,
    #     'newOrderRespType': 'ACK',  # ACK
    # }
    # logging.debug(params)
    # try:
    #     response = client.new_order(**params)
    #     logging.debug(response)
    # except Exception as e:
    #     logging.error(params)
    #     logging.error(e)


def handle_signal(signum, frame):
    # 清仓
    global position
    if position == 1:
        do_order(COIN, Trade.SELL.value, 'MARKET', ORDER_AMOUNT)
        position = 0
    end_time = time.time()
    #绘制监控图像
    plt.hist(obis,bins= 20,edgecolor='black')  # bins参数决定直方图的箱数
    plt.xticks(range(20))
    plt.title('order book imbalance ')
    plt.xlabel("OBI")
    plt.ylabel('Frequency')
    # 显示图形
    plt.show()
    print("FINAL PROFIT:%f" % profit)
    print("Expected profit per day is %f" % ((profit / ((end_time - start_time) / 60)) * 24 * 60))

    # logging.debug("closing ws connection")
    # my_client.stop()
    #
    # sys.exit()


class Trade(enum.Enum):
    BUY = 'BUY'
    SELL = 'SELL'


if __name__ == '__main__':
    # print_profit()
    ip = get_current_proxy_ip()
    print("当前代理 IP:", ip)
    # 注册信号处理程序ctrlz+c
    signal.signal(signal.SIGTSTP, handle_signal)
    # signal.signal(signal.SIGINT, handle_signal)

    # 获取账号:ip_search.py
    # client = Client(api_key='Ng4rh2vG90dbfjVXPAzRYPaLpGcWXuSTcxZqmNKtEXyvl1iqwUKeRG6PPqfdUkDZ',
    #                 api_secret='XxExX9qAXtvKE0aAiP4CiFer8qnF4sxlcoXLNCMFFu7CfTMi95SyOS82I2a5QAVc')
    # logging.debug(client.user_asset())
    # init global vaariables
    # trade = client.my_trades(symbol=COIN, limit=1)[0]
    # if trade["isBuyer"]:
    #     position = 1
    #     buy_in_price = float(trade['price'])
    # 开始运行
    my_client = SpotWebsocketStreamClient(on_message=message_handler)

    my_client.partial_book_depth(symbol=COIN, level=20, speed=100)

    start_time = time.time()

    #
    # logging.debug("closing ws connection")
    # my_client.stop()
