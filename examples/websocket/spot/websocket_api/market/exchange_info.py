#!/usr/bin/env python

import logging
import time
from docs.binance.lib.utils import config_logging
from docs.binance.websocket import SpotWebsocketAPIClient

config_logging(logging, logging.DEBUG)


def on_close(_):
    logging.info("Do custom stuff when connection is closed")


def message_handler(_, message):
    logging.info(message)


my_client = SpotWebsocketAPIClient(on_message=message_handler, on_close=on_close)


my_client.exchange_info(symbol="BNBBUSD")

time.sleep(2)

my_client.exchange_info(symbols=["BNBUSDT", "BTCUSDT"])

time.sleep(2)

my_client.exchange_info(permissions=["SPOT", "MARGIN"])

time.sleep(2)

my_client.exchange_info()

time.sleep(2)

logging.info("closing ws connection")
my_client.stop()
