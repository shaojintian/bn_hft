#!/usr/bin/env python

import logging
from docs.binance.spot import Spot as Client
from docs.binance.lib.utils import config_logging
from docs.prepare_env import get_api_key

config_logging(logging, logging.DEBUG)

api_key, api_secret = get_api_key()


client = Client(api_key, api_secret)
logging.info(client.bswap_liquidity_remove("2", "SINGLE", ["BUSD"], "12415"))
logging.info(
    client.bswap_liquidity_remove("2", "COMBINATION", ["BUSD", "USDT"], "12415")
)
