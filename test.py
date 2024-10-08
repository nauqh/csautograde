import requests

reqUrl = "http://127.0.0.1:8000/test"

headersList = {
    "Accept": "*/*",
    "User-Agent": "Thunder Client (https://www.thunderclient.com)"
}

payload = ""

response = requests.request("GET", reqUrl, data=payload,  headers=headersList)

print(response.json()['summary'])
