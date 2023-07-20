import responses

from docs.binance.spot import Spot as Client
from tests.util import random_str
from tests.util import mock_http_response
from docs.binance import ParameterRequiredError

mock_item = {"key_1": "value_1", "key_2": "value_2"}
mock_exception = {"code": -1, "msg": "error message"}

key = random_str()
secret = random_str()
listen_key = random_str()


def test_renew_isolated_margin_listen_key_without_symbol():
    """Tests the API endpoint to renew an isolated margin listen key without symbol"""

    param = {"symbol": "", "listenKey": listen_key}
    client = Client(key, secret)
    client.renew_isolated_margin_listen_key.when.called_with(**param).should.throw(
        ParameterRequiredError
    )


def test_renew_isolated_margin_listen_key_without_listen_key():
    """Tests the API endpoint to renew an isolated margin listen key without listenkey"""

    param = {"symbol": "", "listenKey": listen_key}
    client = Client(key, secret)
    client.renew_isolated_margin_listen_key.when.called_with(**param).should.throw(
        ParameterRequiredError
    )


@mock_http_response(
    responses.PUT,
    "/sapi/v1/userDataStream/isolated\\?listenKey=" + listen_key + "&symbol=BTCUSDT",
    mock_item,
    200,
)
def test_new_isolated_margin_listen_key():
    """Tests the API endpoint to renew an isolated margin listen key"""

    param = {"symbol": "BTCUSDT", "listenKey": listen_key}
    client = Client(key)
    response = client.renew_isolated_margin_listen_key(**param)
    response.should.equal(mock_item)
