#!/usr/bin/env python

import logging
import time
from docs.binance.lib.utils import config_logging
from docs.binance.websocket import SpotWebsocketAPIClient
from docs.prepare_env import get_api_key

api_key, api_secret = get_api_key()

config_logging(logging, logging.DEBUG)


def on_close(_):
    logging.info("Do custom stuff when connection is closed")


def message_handler(_, message):
    logging.info(message)


my_client = SpotWebsocketAPIClient(
    stream_url="wss://testnet.binance.vision/ws-api/v3",
    api_key=api_key,
    api_secret=api_secret,
    on_message=message_handler,
    on_close=on_close,
)


my_client.user_data_stop(listenKey="your_listen_key")

time.sleep(100)

logging.info("closing ws connection")
my_client.stop()
