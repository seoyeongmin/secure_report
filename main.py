import requests
from bs4 import BeautifulSoup
import json
import os

# GitHub Secrets에서 키와 토큰을 불러옵니다.
REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")
REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")

KISA_URL = "https://www.kisa.or.kr/2060207"
LAST_POST_FILE = "last_kisa_post.txt"

def get_latest_post():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }
    response = requests.get(KISA_URL, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    post_element = soup.select_one('tbody tr td.left a') 
    if post_element:
        title = post_element.text.strip()
        link = "https://www.kisa.or.kr" + post_element['href']
        return title, link
    return None, None

def get_new_access_token():
    url = "https://kauth.kakao.com/oauth/token"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN
    }
    response = requests.post(url, data=data)
    result = response.json()
    return result.get("access_token")

def send_kakao_message(text, link, access_token):
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}
    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": text,
            "link": {"web_url": link, "mobile_web_url": link},
            "button_title": "가이드라인 원문 보기"
        })
    }
    requests.post(url, headers=headers, data=data)

def main():
    title, link = get_latest_post()
    if not title:
        print("게시물 수집 실패")
        return

    # 중복 알림 방지 확인
    if os.path.exists(LAST_POST_FILE):
        with open(LAST_POST_FILE, "r", encoding="utf-8") as f:
            last_title = f.read().strip()
        if title == last_title:
            print("새로운 게시물이 없습니다.")
            return

    # 새 글일 경우 토큰 갱신 및 메시지 발송
    access_token = get_new_access_token()
    if access_token:
        summary_text = f"📋 [KISA 신규 가이드라인]\n\n{title}"
        send_kakao_message(summary_text, link, access_token)
        
        # 발송 완료 후 새 제목을 텍스트 파일에 덮어쓰기
        with open(LAST_POST_FILE, "w", encoding="utf-8") as f:
            f.write(title)
        print(f"✅ 알림 전송 및 기록 완료: {title}")
    else:
        print("❌ 액세스 토큰 발급 실패")

if __name__ == "__main__":
    main()
