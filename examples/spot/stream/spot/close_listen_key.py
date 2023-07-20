#!/usr/bin/env python

import logging
from docs.binance.spot import Spot as Client
from docs.binance.lib.utils import config_logging
from docs.prepare_env import get_api_key

config_logging(logging, logging.DEBUG)

api_key, _ = get_api_key()

client = Client(api_key, base_url="https://testnet.binance.vision")
logging.info(client.close_listen_key(""))
