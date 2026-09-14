import requests

REST_API_KEY = "YOUR_REST_API_KEY"
REDIRECT_URI = "https://localhost"
AUTHORIZATION_CODE = "YOUR_AUTHORIZATION_CODE"  # 카카오 로그인 후 발급받은 인가 코드

def get_refresh_token():
    url = "[https://kauth.kakao.com/oauth/token](https://kauth.kakao.com/oauth/token)"
    data = {
        "grant_type": "authorization_code",
        "client_id": REST_API_KEY,
        "redirect_uri": REDIRECT_URI,
        "code": AUTHORIZATION_CODE
    }
    response = requests.post(url, data=data)
    print(response.json())

if __name__ == "__main__":
    get_refresh_token()
