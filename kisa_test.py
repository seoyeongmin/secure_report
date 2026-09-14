import requests
import json

# --- 1. 초기 설정값 ---
REST_API_KEY = "f5b645ac0ad7d128fe49ba8a16dfcd42"
REFRESH_TOKEN = "UfVqWzEJbQRgzgry0DYzS--4vgrzT2yNAAAAAgoNG1kAAAGgnhjE8FXuKbObXTiX"

def get_new_access_token():
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN
    }
    response = requests.post(url, data=data)
    result = response.json()
    
    if "access_token" in result:
        return result["access_token"]
    else:
        print("❌ 토큰 갱신 실패:", result)
        return None

def send_kakao_message(text, access_token):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text,
            "link": {
                "web_url": "https://www.kisa.or.kr/2060207",
                "mobile_web_url": "https://www.kisa.or.kr/2060207"
            },
            "button_title": "가이드라인 원문 보기"
        })
    }
    
    response = requests.post(url, headers=headers, data=data)
    if response.status_code == 200:
        print("✅ 카카오톡 메시지 전송 성공!")
    else:
        print("❌ 전송 실패:", response.text)

# --- 2. 실행 테스트 ---
new_token = get_new_access_token()
if new_token:
    send_kakao_message("📋 [KISA 신규 가이드라인 알림 테스트]", new_token)