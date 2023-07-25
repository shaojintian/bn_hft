import requests

def get_usdt_pairs():
    url = "https://api.binance.com/api/v3/ticker/price"
    params = {"symbol": "USDT"}

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        usdt_pairs = [pair["symbol"] for pair in data]
        return usdt_pairs
    else:
        print("Failed to fetch data from Binance API.")
        return []

usdt_pairs_list = get_usdt_pairs()
print(usdt_pairs_list)
