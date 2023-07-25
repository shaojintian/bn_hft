import requests

def get_high_volume_contract_codes():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    params = {
        "limit": 50,   # You can adjust the limit to get more or fewer symbols
        "sort": "desc",  # Sort by descending volume
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        high_volume_contracts = [item["symbol"] for item in data]
        return high_volume_contracts
    else:
        print(f"Failed to fetch data. Status code: {response.status_code}")
        return []

if __name__ == "__main__":
    high_volume_contracts = get_high_volume_contract_codes()
    print(high_volume_contracts)
