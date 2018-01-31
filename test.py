import requests
import json
import time

url = "http://192.168.1.168"

for i in range(1000):
    data = json.loads(requests.get("http://192.168.1.168/request_data").text)
    print(data["Temp"], flush=True)
    
    