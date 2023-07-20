#!/usr/bin/env python

import logging
from docs.binance.spot import Spot as Client
from docs.binance.lib.utils import config_logging

config_logging(logging, logging.DEBUG)

spot_client = Client(base_url="https://testnet.binance.vision")

logging.info(spot_client.ticker_price("BTCUSDT"))
logging.info(spot_client.ticker_price(symbols=["BTCUSDT", "BNBUSDT"]))
