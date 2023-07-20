from docs.binance.websocket.websocket_client import BinanceWebsocketClient


class SpotWebsocketAPIClient(BinanceWebsocketClient):
    def __init__(
        self,
        stream_url="wss://ws-api.binance.com/ws-api/v3",
        api_key=None,
        api_secret=None,
        on_message=None,
        on_open=None,
        on_close=None,
        on_error=None,
        on_ping=None,
        on_pong=None,
    ):
        self.api_key = api_key
        self.api_secret = api_secret

        super().__init__(
            stream_url,
            on_message=on_message,
            on_open=on_open,
            on_close=on_close,
            on_error=on_error,
            on_ping=on_ping,
            on_pong=on_pong,
        )

    # Market
    from docs.binance.websocket.spot.websocket_api._market import ping_connectivity
    from docs.binance.websocket.spot.websocket_api._market import server_time
    from docs.binance.websocket.spot.websocket_api._market import exchange_info
    from docs.binance.websocket.spot.websocket_api._market import order_book
    from docs.binance.websocket.spot.websocket_api._market import recent_trades
    from docs.binance.websocket.spot.websocket_api._market import historical_trades
    from docs.binance.websocket.spot.websocket_api._market import aggregate_trades
    from docs.binance.websocket.spot.websocket_api._market import klines
    from docs.binance.websocket.spot.websocket_api._market import ui_klines
    from docs.binance.websocket.spot.websocket_api._market import avg_price
    from docs.binance.websocket.spot.websocket_api._market import ticker_24hr
    from docs.binance.websocket.spot.websocket_api._market import ticker
    from docs.binance.websocket.spot.websocket_api._market import ticker_price
    from docs.binance.websocket.spot.websocket_api._market import ticker_book

    # Account

    # Trade

    # User Data Stream

