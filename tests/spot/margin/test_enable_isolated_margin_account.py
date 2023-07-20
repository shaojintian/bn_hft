import responses
from urllib.parse import urlencode
from tests.util import random_str
from tests.util import mock_http_response
from docs.binance.spot import Spot as Client
from docs.binance import ParameterRequiredError

mock_item = {"key_1": "value_1", "key_2": "value_2"}
mock_exception = {"code": -1, "msg": "error message"}

key = random_str()
secret = random_str()

params = {
    "symbol": "BTCUSDT",
    "recvWindow": 1000,
}

client = Client(key, secret)


def test_enable_isolated_margin_account_without_symbol():
    """Tests the API endpoint to enable an isolated margin account without symbol"""

    client.enable_isolated_margin_account.when.called_with("").should.throw(
        ParameterRequiredError
    )


@mock_http_response(
    responses.POST,
    "/sapi/v1/margin/isolated/account\\?" + urlencode(params),
    mock_item,
    200,
)
def test_enable_isolated_margin_account():
    """Tests the API endpoint to enable an isolated margin account"""

    response = client.enable_isolated_margin_account(**params)
    response.should.equal(mock_item)
