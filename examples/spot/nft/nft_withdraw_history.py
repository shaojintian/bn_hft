#!/usr/bin/env python

import logging
from docs.binance.spot import Spot as Client
from docs.binance.lib.utils import config_logging
from docs.binance import ClientError
from docs.prepare_env import get_api_key

config_logging(logging, logging.DEBUG)

api_key, api_secret = get_api_key()

client = Client(api_key, api_secret)
logger = logging.getLogger(__name__)

try:
    logger.info(
        client.nft_withdraw_history(
            startTime=1636887168000, endTime=1639479168000, limit=50
        )
    )
except ClientError as error:
    logger.error(
        "Found error. status: {}, error code: {}, error message: {}".format(
            error.status_code, error.error_code, error.error_message
        )
    )
