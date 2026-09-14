import requests
from bs4 import BeautifulSoup
import json
import os

REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")
REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")

def get_access_token():
    url = "[https://kauth.kakao.com/oauth/token](https://kauth.kakao.com/oauth/token)"
    data = {
        "grant_type": "refresh_token",
        "client_id": REST_API_KEY,
        "refresh_token": REFRESH_TOKEN
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")

def test_kisa_crawl():
    url = "[https://www.kisa.or.kr/2060207](https://www.kisa.or.kr/2060207)"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')
    post = soup.select_one('tbody tr td.left a')
    
    title = post.text.strip()
    link = "[https://www.kisa.or.kr](https://www.kisa.or.kr)" + post['href']
    print(f"추출된 제목: {title}")
    print(f"추출된 링크: {link}")

if __name__ == "__main__":
    test_kisa_crawl()
