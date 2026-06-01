import json
import urllib.request
import urllib.error
import sys

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/chat"
data = {
    "messages": [
        {"role": "user", "content": "Xin chào! Bạn là ai?"}
    ],
    "temperature": 0.7
}

req = urllib.request.Request(
    url,
    data=json.dumps(data).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST"
)

print(f"Sending POST request to FastAPI backend at {url}...")
try:
    with urllib.request.urlopen(req) as response:
        status_code = response.getcode()
        body = response.read().decode("utf-8")
        print(f"Status Code: {status_code}\n")
        
        response_json = json.loads(body)
        print("--- Response body from FastAPI ---")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        print("---------------------------------")
except urllib.error.HTTPError as e:
    print(f"HTTP Error: {e.code} - {e.reason}")
    print(e.read().decode("utf-8"))
except Exception as e:
    print(f"An error occurred: {e}")
