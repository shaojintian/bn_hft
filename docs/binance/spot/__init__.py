from docs.binance.api import API


class Spot(API):
    def __init__(self, api_key=None, api_secret=None, **kwargs):
        if "base_url" not in kwargs:
            kwargs["base_url"] = "https://api.binance.com"
        super().__init__(api_key, api_secret, **kwargs)

    # MARKETS

    # ACCOUNT (including orders and trades)

    # STREAMS

    # MARGIN

    # SAVINGS

    # Staking

    # WALLET

    # MINING

    # SUB-ACCOUNT

    # FUTURES

    # BLVTs

    # BSwap

    # FIAT

    # C2C

    # LOANS

    # PAY
    from docs.binance.spot._pay import pay_history

    # CONVERT

    # REBATE

    # NFT

    # Gift Card (Binance Code in the API documentation)

    # Portfolio Margin

