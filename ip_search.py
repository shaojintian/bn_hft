import requests

def get_current_proxy_ip():
    response = requests.get("https://api.ipify.org?format=json")
    ip_data = response.json()
    return ip_data["ip"]

current_proxy_ip = get_current_proxy_ip()
print("当前代理 IP:", current_proxy_ip)
