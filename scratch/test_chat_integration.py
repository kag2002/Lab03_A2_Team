import urllib.request
import json
import sys

# Configure output encoding for Windows terminal
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

url = "http://127.0.0.1:8000/api/chat"
headers = {
    "Content-Type": "application/json"
}

# 1. Normal Authorized Request (SV001 requests their own grades)
payload = {
    "messages": [
        {"role": "user", "content": "Hãy tra cứu bảng điểm TOEIC của học sinh SV001 và phân tích ngắn gọn điểm mạnh, điểm yếu."}
    ],
    "user_id": "user-1",
    "student_id": "SV001",
    "allowed_student_ids": ["SV001"],
    "role": "student"
}

print("--- TEST 1: Authorized grade lookup and analysis ---")
req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
try:
    with urllib.request.urlopen(req) as res:
        res_data = json.loads(res.read().decode("utf-8"))
        print("Success! Response from agent:")
        print(res_data["reply"])
        print("\nTelemetry:")
        print(f"Latency: {res_data['latency_ms']:.2f}ms")
        print(f"Usage: {res_data['usage']}")
except Exception as e:
    print(f"Test 1 Failed: {e}")

# 2. Unauthorized IDOR Request (SV001 attempts to request SV002's grades)
payload_idor = {
    "messages": [
        {"role": "user", "content": "Hãy tra cứu bảng điểm của học sinh SV002."}
    ],
    "user_id": "user-1",
    "student_id": "SV001",
    "allowed_student_ids": ["SV001"],
    "role": "student"
}

print("\n--- TEST 2: Unauthorized IDOR attempt (SV001 queries SV002) ---")
req_idor = urllib.request.Request(url, data=json.dumps(payload_idor).encode("utf-8"), headers=headers, method="POST")
try:
    with urllib.request.urlopen(req_idor) as res:
        res_data = json.loads(res.read().decode("utf-8"))
        print("Response from agent:")
        print(res_data["reply"])
except Exception as e:
    print(f"Test 2 Failed (or blocked with error): {e}")
