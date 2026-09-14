import requests

AUTH_CODE = "Skix7pBeTSaf90OHSAzmW29QyXMKX4XbgK4DjvOvBBBnC8ryoHlz5gAAAAQKDR-XAAABoJ4Xg2Iq3eF1vjqPRg"

url = "https://kauth.kakao.com/oauth/token"
data = {
    "grant_type": "authorization_code",
    "client_id": "f5b645ac0ad7d128fe49ba8a16dfcd42",
    "redirect_uri": "http://localhost:3000",
    "code": AUTH_CODE
}

response = requests.post(url, data=data)
result = response.json()

print("\n=== 발급 결과 ===")
if "refresh_token" in result:
    print(f"👉 리프레시 토큰: {result['refresh_token']}\n")
    print("성공! 이 값을 kisa_test.py의 REFRESH_TOKEN 자리에 넣으세요.")
else:
    print(f"❌ 실패 원인: {result}")