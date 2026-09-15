import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import urllib3

# SSL 경고 무시 설정
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# GitHub Secrets에서 키와 토큰 불러오기
REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")
REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")

# 파일 경로 설정 (사이트별 중복 방지 기록 파일)
KISA_FILE = "last_kisa_post.txt"
NEWS_FILE = "last_news_post.txt"
PIPC_FILE = "last_pipc_post.txt"
HISTORY_FILE = "alert_history.txt"

# 공통 브라우저 헤더 (전역 선언)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"
}

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

def clean_text(element):
    """[공통 함수] BeautifulSoup 요소나 문자열에서 'N' 마크 및 불필요한 공백을 제거합니다."""
    if not element:
        return ""
    text = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element).strip()
    return text.replace('N', '').strip()

def send_kakao_message(header, description, link, access_token):
    """카카오톡 '나에게 보내기' 텍스트 템플릿 전송 함수"""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    full_text = f"━━━━━━━━━━━━━━━━\n{header}\n━━━━━━━━━━━━━━━━\n\n{description}\n\n🔗 [원문 바로가기]\n{link}"
    
    data = {
        "template_object": json.dumps({
            "object_type": "text",
            "text": full_text,
            "link": {
                "web_url": link,
                "mobile_web_url": link
            }
        })
    }
    response = requests.post(url, headers=headers, data=data)
    return response.json()

def log_history(category, title):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{now}] [{category}] {title}\n"
    
    history_content = ""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history_content = f.read()
            
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write(log_entry + history_content)

# 1. KISA 가이드라인 체크
def check_kisa(access_token):
    url = "https://www.kisa.or.kr/2060207"
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = soup.select('tbody tr')
        
        if not posts:
            print("ℹ️ KISA 게시물 목록을 찾지 못했습니다.")
            return
        
        last_title = ""
        if os.path.exists(KISA_FILE):
            with open(KISA_FILE, "r", encoding="utf-8") as f:
                last_title = f.read().strip()

        for row in posts:
            post = row.select_one('td.left a')
            if not post:
                continue
            
            title = clean_text(post)
            href = post.get('href', '')
            link = "https://www.kisa.or.kr" + href if href.startswith('/') else href
            description = f"{title}"

            if title == last_title:
                print("ℹ️ [KISA] 이미 발송된 최신 게시물과 동일하여 메시지를 전송하지 않습니다.")
                break

            header = "📋 KISA 가이드라인 알림"
            send_kakao_message(header, description, link, access_token)
            log_history("KISA", title)
            with open(KISA_FILE, "w", encoding="utf-8") as f:
                f.write(title)
            print(f"✅ KISA 알림 전송: {title}")
            break
        else:
            print("ℹ️ KISA 신규 게시물 없음")
    except Exception as e:
        print(f"❌ KISA 확인 중 에러: {e}")

# 2. 보안뉴스 체크 (제공해주신 HTML 구조 반영: auto-titles 및 articleView.html?idxno= 탐색)
def check_security_news(access_token):
    KEYWORDS = ["개인정보 유출", "api key", "협력사", "해킹", "공급망", "ISMS", "ISO", "SOC"]
    url = "https://www.boannews.com/"
    
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = []
        # HTML에 명시된 기사 제목 태그(<H2 class="auto-titles...">)를 포함하는 a 태그들을 수집
        for h2 in soup.select('h2.auto-titles'):
            a_tag = h2.find_parent('a') or h2.select_one('a')
            if not a_tag:
                # h2의 조상 중 a 태그가 있는지 탐색
                a_tag = h2.find_previous('a', href=True)
            
            if not a_tag:
                continue
                
            href = a_tag.get('href', '')
            if 'articleView.html?idxno=' not in href:
                continue
                
            title = clean_text(h2)
            if not title or len(title) < 5:
                continue
                
            link = "https://www.boannews.com/news/" + href if not href.startswith('http') else href
            articles.append((title, link))

        # 혹시 위 방식으로 못 잡을 경우를 대비한 백업 셀렉터 (articleView 링크가 걸린 모든 a 태그 탐색)
        if not articles:
            for a in soup.select('a[href*="articleView.html?idxno="]'):
                title = clean_text(a)
                href = a.get('href', '')
                if not title or len(title) < 5:
                    continue
                link = "https://www.boannews.com/" + href if not href.startswith('http') else href
                articles.append((title, link))

        # 중복 제거
        seen_titles = set()
        unique_articles = []
        for t, l in articles:
            if t not in seen_titles:
                seen_titles.add(t)
                unique_articles.append((t, l))

        if not unique_articles:
            print("ℹ️ 보안뉴스 목록을 찾지 못했습니다.")
            return

        last_news = ""
        if os.path.exists(NEWS_FILE):
            with open(NEWS_FILE, "r", encoding="utf-8") as f:
                last_news = f.read().strip()

        for title, link in unique_articles:
            if title == last_news:
                print("ℹ️ [보안뉴스] 이미 발송된 최신 기사와 동일하여 메시지를 전송하지 않습니다.")
                break

            matched_keyword = next((kw for kw in KEYWORDS if kw.lower() in title.lower()), None)
            if matched_keyword:
                header = f"🚨 보안뉴스 [{matched_keyword}]"
                description = f"{title}\n\n[상세 내용 및 본문은 원문 링크를 참고하세요]"
                
                send_kakao_message(header, description, link, access_token)
                log_history("보안뉴스", title)
                print(f"✅ 보안뉴스 전송 [{matched_keyword}]: {title}")
                
                with open(NEWS_FILE, "w", encoding="utf-8") as f:
                    f.write(title)
                break
        else:
            print("ℹ️ 조건에 맞는 새로운 보안뉴스 없음")
    except Exception as e:
        print(f"❌ 보안뉴스 확인 중 에러: {e}")

# 3. 개인정보보호위원회(PIPC) 체크
def check_pipc(access_token):
    KEYWORDS = ["제재", "통과", "의결", "시행", "부과", "법", "위반", "시행령", "처분"]
    url = "https://pipc.go.kr/np/cop/bbs/selectBoardList.do?bbsId=BS074&mCode=C020010000"
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = soup.select('tbody tr')
        
        if not posts:
            print("ℹ️ PIPC 게시물 목록을 찾지 못했습니다.")
            return

        last_pipc = ""
        if os.path.exists(PIPC_FILE):
            with open(PIPC_FILE, "r", encoding="utf-8") as f:
                last_pipc = f.read().strip()

        for row in posts:
            a_tag = row.select_one('td.left a') or row.select_one('a')
            if not a_tag:
                continue
            
            title = clean_text(a_tag)
            href = a_tag.get('href', '#')
            link = "https://pipc.go.kr" + href if href.startswith('/') else href

            if title == last_pipc:
                print("ℹ️ [PIPC] 이미 발송된 최신 게시물과 동일하여 메시지를 전송하지 않습니다.")
                break

            matched_keyword = next((kw for kw in KEYWORDS if kw.lower() in title.lower()), None)
            if matched_keyword:
                header = f"🏛️ 개인정보보호위원회 [{matched_keyword}]"
                description = f"{title}"
                
                send_kakao_message(header, description, link, access_token)
                log_history("PIPC", title)
                print(f"✅ PIPC 전송 [{matched_keyword}]: {title}")
                
                with open(PIPC_FILE, "w", encoding="utf-8") as f:
                    f.write(title)
                break
        else:
            print("ℹ️ 조건에 맞는 새로운 PIPC 게시물 없음")
    except Exception as e:
        print(f"❌ PIPC 확인 중 에러: {e}")

def main():
    access_token = get_new_access_token()
    if not access_token:
        print("❌ 액세스 토큰 갱신 실패")
        return

    print("--- 3대 보안 소스 봇 실행 시작 ---")
    
    try:
        check_kisa(access_token)
    except Exception as e:
        print(f"❌ KISA 실행 중 예외 발생: {e}")
        
    try:
        check_security_news(access_token)
    except Exception as e:
        print(f"❌ 보안뉴스 실행 중 예외 발생: {e}")
        
    try:
        check_pipc(access_token)
    except Exception as e:
        print(f"❌ PIPC 실행 중 예외 발생: {e}")
        
    print("--- 3대 보안 소스 봇 실행 완료 ---")

if __name__ == "__main__":
    main()
