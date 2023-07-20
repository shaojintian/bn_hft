#!/usr/bin/env python

import logging
from docs.binance.spot import Spot as Client
from docs.binance.lib.utils import config_logging
from docs.binance import ClientError

config_logging(logging, logging.DEBUG)


client = Client()

try:
    response = client.rolling_window_ticker("BNBUSDT", windowSize="1d", type="MINI")
    logging.info(response)
except ClientError as error:
    logging.error(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )
