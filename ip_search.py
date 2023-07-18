import requests

def get_current_proxy_ip():
    response = requests.get("https://api.ipify.org?format=json")
    ip_data = response.json()
    return ip_data["ip"]


