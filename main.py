#!/usr/bin/env python
import threading
import signal
import time
import logging
import json
import enum
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient
from binance.spot import Spot as Client

config_logging(logging, logging.ERROR)

# 买入比例
LOB_THRESHOLD = 0

COIN = "BTCTUSD"

ORDER_AMOUNT = 0.01

profit = 0

position = 0

buy_in_price = 0


def message_handler(_, message):
    # print(message)
    data_dict = json.loads(message)
    bids_quantities = sum([float(bid[1]) for bid in data_dict["bids"]])
    asks_quantities = sum([float(ask[1]) for ask in data_dict["asks"]])

    bid_1 = float(data_dict["bids"][0][0])
    ask_1 = float(data_dict["asks"][0][0])

    # bid_1_quantity = float(data_dict["bids"][0][1])
    # ask_1_quantity = float(data_dict["asks"][0][1])
    # lob_now = bids_quantities / asks_quantities
    # print(bids_quantities / asks_quantities)
    global buy_in_price, profit, position, ORDER_AMOUNT

    # stop loss = 5-1000 * 0.01 = 0.05u-10u
    is_shut_down = (buy_in_price - ask_1) > 1000
    is_stop_loss = (buy_in_price - ask_1) > 5

    if position == 0:
        buy_in_price = bid_1
        # float(data_dict["bids"][0][1])
        # 下单
        do_order(COIN,Trade.BUY.value, 'LIMIT',ORDER_AMOUNT,buy_in_price)
        # print("BID BUY: price:%f amount:%f"% (buy_in_price, order_amount))
        #
        position = 1
    elif position == 1 and ask_1 > buy_in_price:
        # 下单止盈
        # print("BID SELL: price:%f amount:%f"% (ask_1, order_amount))
        do_order(COIN, Trade.SELL.value, 'LIMIT',ORDER_AMOUNT, ask_1)
        profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
        print("Profit:%f" % profit)
        #
        buy_in_price = 0
        position = 0
    elif position == 1 and is_shut_down:
        # 下单停机
        print("SHUTDOWN ON TRAILING ORDER: buy in:%f price:%f amount:%f！！！！！\n" % (
            buy_in_price, ask_1, ORDER_AMOUNT))
        do_order(COIN, Trade.SELL.value, 'LIMIT',ORDER_AMOUNT, ask_1)
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
        print("STOP LOSS ON TRAILING ORDER: buy in:%f price:%f amount:%f！！！！！\n" % (buy_in_price, ask_1, ORDER_AMOUNT))
        # print("LOB RATIO IS: %f" % lob_now)
        do_order(COIN, Trade.SELL.value, 'LIMIT',ORDER_AMOUNT, ask_1)
        profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
        # print("Profit:%f" % profit)
        buy_in_price = 0
        position = 0


def do_order(symbol=COIN, side="SELL", _type='LIMIT',quantity=ORDER_AMOUNT, price=None):
    # Post a new order
    params = {
        'symbol': symbol,
        'side': side,
        'type': _type,
        'timeInForce': 'GTC',
        'quantity': quantity,
        'price': price,
        'newOrderRespType':'ACK',
    }
    logging.debug(params)
    response = client.new_order_test(**params)


def handle_signal(signum, frame):
    # 在这里编写你想要触发的函数或操作
    # 清仓
    global position
    if position == 1:
        do_order(COIN, Trade.SELL.value, 'MARKET',ORDER_AMOUNT)
        position = 0
    end_time = time.time()
    print("FINAL PROFIT:%f" % profit)
    print("Expected profit per day is %f" % ((profit / ((end_time - start_time) / 60)) * 24 * 60))

    logging.debug("closing ws connection")
    my_client.stop()


class Trade(enum.Enum):
    BUY = 'BUY'
    SELL = 'SELL'

if __name__ == '__main__':
    # print_profit()
    # 注册信号处理程序ctrlz+c
    signal.signal(signal.SIGTSTP, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # 获取账号:ip_search.py
    client = Client(api_key='Ng4rh2vG90dbfjVXPAzRYPaLpGcWXuSTcxZqmNKtEXyvl1iqwUKeRG6PPqfdUkDZ',
                    api_secret='XxExX9qAXtvKE0aAiP4CiFer8qnF4sxlcoXLNCMFFu7CfTMi95SyOS82I2a5QAVc')
    logging.debug(client.user_asset())
    # 开始运行
    my_client = SpotWebsocketStreamClient(on_message=message_handler)

    my_client.partial_book_depth(symbol=COIN, level=20, speed=100)

    start_time = time.time()

    #
    # logging.debug("closing ws connection")
    # my_client.stop()
