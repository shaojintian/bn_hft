#!/usr/bin/env python
import threading
import signal
import time
import logging
import json
from binance.lib.utils import config_logging
from binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

config_logging(logging, logging.DEBUG)

# 买入比例
LOB_THRESHOLD = 0

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
        # print("BID BUY: price:%f amount:%f"% (buy_in_price, order_amount))
        #
        position = 1
    elif position == 1 and ask_1 > buy_in_price:
        # 下单止盈
        # print("BID SELL: price:%f amount:%f"% (ask_1, order_amount))
        profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
        print("Profit:%f" % profit)
        #
        buy_in_price = 0
        position = 0
    elif position == 1 and is_shut_down:
        # 下单停机
        print("SHUTDOWN LOSS ON TRAILING ORDER: buy in:%f price:%f amount:%f！！！！！\n" % (
            buy_in_price, ask_1, ORDER_AMOUNT))
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
        profit += (ask_1 - buy_in_price) * ORDER_AMOUNT
        # print("Profit:%f" % profit)
        buy_in_price = 0
        position = 0


def handle_signal(signum, frame):
    # 在这里编写你想要触发的函数或操作
    # 清仓

    end_time = time.time()
    print("FINAL PROFIT:%f" % profit)
    print("Expected profit per day is %f" % ((profit / ((end_time - start_time) / 60)) * 24 * 60))

    logging.debug("closing ws connection")
    my_client.stop()


if __name__ == '__main__':
    #
    # print_profit()
    # 注册信号处理程序ctrlz
    signal.signal(signal.SIGTSTP, handle_signal)

    my_client = SpotWebsocketStreamClient(on_message=message_handler)

    my_client.partial_book_depth(symbol="btctusd", level=20, speed=100)

    start_time = time.time()

    #
    # logging.debug("closing ws connection")
    # my_client.stop()
