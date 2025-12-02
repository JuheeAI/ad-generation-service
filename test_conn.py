# test_conn.py
import requests

try:
    print("1. http://127.0.0.1:9000 연결 시도 중...")
    r = requests.get("http://127.0.0.1:9000/", timeout=5)
    print(f"✅ 성공! 상태 코드: {r.status_code}")
    print(f"   응답 내용: {r.text}")
except Exception as e:
    print(f"❌ 127.0.0.1 실패: {e}")

print("-" * 20)

try:
    print("2. http://localhost:9000 연결 시도 중...")
    r = requests.get("http://localhost:9000/", timeout=5)
    print(f"✅ 성공! 상태 코드: {r.status_code}")
except Exception as e:
    print(f"❌ localhost 실패: {e}")