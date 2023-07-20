#!/usr/bin/env python

import logging
from docs.binance.spot import Spot as Client
from docs.binance.lib.utils import config_logging
from docs.prepare_env import get_api_key

config_logging(logging, logging.DEBUG)

api_key, api_secret = get_api_key()

logger = logging.getLogger(__name__)
spot_client = Client(api_key, api_secret, show_header=True)
logging.info(spot_client.bnb_convertible_assets())
