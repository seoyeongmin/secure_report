import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# GitHub Secrets에서 키와 토큰 불러오기
REST_API_KEY = os.environ.get("KAKAO_REST_API_KEY")
REFRESH_TOKEN = os.environ.get("KAKAO_REFRESH_TOKEN")

# 파일 경로 설정 (사이트별 중복 방지 기록 파일)
KISA_FILE = "last_kisa_post.txt"
NEWS_FILE = "last_news_post.txt"
PIPC_FILE = "last_pipc_post.txt"
HISTORY_FILE = "alert_history.txt"

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

def send_kakao_message(header, description, link, access_token):
    """카카오톡 '나에게 보내기' 텍스트 템플릿을 활용해 
    상세 내용이 잘리지 않고 원문 링크와 함께 완벽히 출력되도록 전송합니다."""
    url = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 텍스트 내부에 구분선, 전체 상세 설명, 원문 링크를 명확히 구성
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

# 1. KISA 가이드라인 체크 (N 제거 및 정제 적용)
def check_kisa(access_token):
    url = "https://www.kisa.or.kr/2060207"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, verify=False)
        soup = BeautifulSoup(response.text, 'html.parser')
        post = soup.select_one('tbody tr td.left a')
        if not post:
            return
        
        # 텍스트 추출 후 'N' 마크 및 불필요한 공백 제거
        title = post.get_text(strip=True).replace('N', '').strip()
        link = "https://www.kisa.or.kr" + post['href']
        description = f"{title}"

        last_title = ""
        if os.path.exists(KISA_FILE):
            with open(KISA_FILE, "r", encoding="utf-8") as f:
                last_title = f.read().strip()

        if title != last_title:
            header = "📋 KISA 가이드라인 알림"
            send_kakao_message(header, description, link, access_token)
            log_history("KISA", title)
            with open(KISA_FILE, "w", encoding="utf-8") as f:
                f.write(title)
            print(f"✅ KISA 알림 전송: {title}")
        else:
            print("ℹ️ KISA 신규 게시물 없음")
    except Exception as e:
        print(f"❌ KISA 확인 중 에러: {e}")

# 2. 보안뉴스 체크 (N 제거 및 정제 적용)
# 보안뉴스 체크 (최신 URL 및 셀렉터 반영 버전)
def check_security_news(access_token):
    KEYWORDS = ["개인정보 유출", "api key", "협력사", "해킹", "공급망", "ISMS", "ISO", "SOC"]
    # 보안뉴스 최신 리스트 페이지 주소로 변경
    url = "https://www.boannews.com/media/t_list.asp"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 보안뉴스 최신 목록 태그 구조(.news_list)
        news_items = soup.select('.news_list')
        
        last_news = ""
        if os.path.exists(NEWS_FILE):
            with open(NEWS_FILE, "r", encoding="utf-8") as f:
                last_news = f.read().strip()

        for item in news_items:
            # 제목 및 링크가 들어있는 a 태그 추출
            a_tag = item.select_one('a')
            if not a_tag:
                continue
            
            # span.news_txt 안의 텍스트가 순수 제목
            txt_span = item.select_one('span.news_txt')
            if not txt_span:
                continue
                
            title = clean_text(txt_span)
            
            # 상대 경로를 절대 경로로 변환
            href = a_tag.get('href', '')
            link = "https://www.boannews.com/media/" + href if not href.startswith('http') else href

            # 요약 부가 텍스트
            sub_txt = item.select_one('span.news_sub') # 또는 작성자/요약 영역
            summary = clean_text(sub_txt) if sub_txt else "상세 내용 및 본문은 원문 링크를 확인해주세요."

            if title == last_news:
                break

            matched_keyword = next((kw for kw in KEYWORDS if kw.lower() in title.lower()), None)
            if matched_keyword:
                header = f"🚨 보안뉴스 [{matched_keyword}]"
                description = f"{title}\n\n[요약]\n{summary}"
                
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
        
# 3. 개인정보보호위원회(PIPC) 체크 (N 제거 및 정제 적용)
def check_pipc(access_token):
    KEYWORDS = ["제재", "통과", "의결", "시행", "부과", "법", "위반", "시행령", "처분"]
    url = "https://pipc.go.kr/np/cop/bbs/selectBoardList.do?bbsId=BS074&mCode=C020010000"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, verify=False)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        posts = soup.select('tbody tr')
        
        last_pipc = ""
        if os.path.exists(PIPC_FILE):
            with open(PIPC_FILE, "r", encoding="utf-8") as f:
                last_pipc = f.read().strip()

        for row in posts:
            a_tag = row.select_one('td.left a') or row.select_one('a')
            if not a_tag:
                continue
            
            # 텍스트 추출 후 'N' 마크 및 공백 정제
            title = a_tag.get_text(strip=True).replace('N', '').strip()
            href = a_tag.get('href', '#')
            link = "https://pipc.go.kr" + href if href.startswith('/') else href

            if title == last_pipc:
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

    print("--- 3대 보안 소스 봇 실행 시작 (통합 정제 및 링크 최적화 버전) ---")
    check_kisa(access_token)
    check_security_news(access_token)
    check_pipc(access_token)
    print("--- 3대 보안 소스 봇 실행 완료 ---")

if __name__ == "__main__":
    main()
