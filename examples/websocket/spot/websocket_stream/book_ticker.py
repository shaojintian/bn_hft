#!/usr/bin/env python

import time
import logging
from docs.binance.lib.utils import config_logging
from docs.binance.websocket.spot.websocket_stream import SpotWebsocketStreamClient

config_logging(logging, logging.DEBUG)


def message_handler(_, message):
    print(message)


my_client = SpotWebsocketStreamClient(on_message=message_handler)


my_client.book_ticker(symbol="btcusdt")

time.sleep(10)

logging.debug("closing ws connection")
my_client.stop()
