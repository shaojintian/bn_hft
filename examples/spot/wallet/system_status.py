#!/usr/bin/env python

import logging
from docs.binance.spot import Spot as Client
from docs.binance.lib.utils import config_logging

config_logging(logging, logging.DEBUG)

spot_client = Client()

logging.info(spot_client.system_status())
