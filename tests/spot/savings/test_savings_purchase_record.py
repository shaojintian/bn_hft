import responses

from tests.util import random_str
from tests.util import mock_http_response
from docs.binance.spot import Spot as Client
from docs.binance import ParameterRequiredError

mock_item = {"key_1": "value_1", "key_2": "value_2"}

key = random_str()
secret = random_str()


def test_savings_purchase_record_without_lendingType():
    """Tests the API endpoint to get purchase record without lendingType"""

    client = Client(key, secret)
    client.savings_purchase_record.when.called_with("").should.throw(
        ParameterRequiredError
    )


@mock_http_response(
    responses.GET,
    "/sapi/v1/lending/union/purchaseRecord\\?lendingType=1",
    mock_item,
    200,
)
def test_savings_purchase_record():
    """Tests the API endpoint to get purchase record"""

    client = Client(key, secret)
    response = client.savings_purchase_record(lendingType=1)
    response.should.equal(mock_item)
