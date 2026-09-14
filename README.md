# 🛡️ Multi-Source Security Monitoring & KakaoTalk Bot

> **GitHub Actions**와 **Python**을 활용하여 KISA 가이드라인, 보안뉴스, 개인정보보호위원회(PIPC)의 최신 보안 동향을 실시간으로 수집하고, **카카오톡 나에게 보내기**로 스마트 알림 및 히스토리를 관리하는 자동화 봇 프로젝트입니다.

---

## 📌 주요 기능 (Features)

1. **다중 소스 통합 모니터링**
   - **KISA 가이드라인:** 신규 등록되는 보안 가이드라인 실시간 추적
   - **보안뉴스:** 관심 키워드(`개인정보 유출`, `api key`, `협력사`, `해킹`, `공급망`, `ISMS`, `ISO`, `SOC`) 매칭 기사 필터링
   - **개인정보보호위원회(PIPC):** 주요 고시, 지침, 제·개정 사항 모니터링
2. **카카오톡 스마트 알림 (API 연동)**
   - 단순 텍스트가 아닌, **제목, 요약 본문, 원문 이동 버튼 링크**가 포함된 가독성 높은 형태로 메시지 전송
3. **자동 히스토리 로깅 (`alert_history.txt`)**
   - 알림이 발송될 때마다 날짜와 타임라인을 기록하여 레포지토리에 자동 누적
4. **무중단 서버리스 자동화 (GitHub Actions)**
   - 클라우드 환경(GitHub Actions)을 활용해 **매일 하루 4회(07:00, 09:30, 14:00, 17:00)** 정기 실행 및 수동 실행 지원

---

## ⚙️ 시스템 아키텍처 (Architecture)

```text
[GitHub Actions (Cron 스케줄러)] 
       │ (정해진 시간에 자동 실행)
       ▼
  [main.py 실행] ──> 3대 보안 사이트 크롤링 (BeautifulSoup)
       │
       ├─> 신규 게시물 및 키워드 매칭 검사
       ├─> 중복 방지 파일 대조 (last_*_post.txt)
       │
       ├─ (알림 발생 시) ──> 카카오톡 API (나에게 보내기) 전송
       └─ (히스토리 갱신) ──> alert_history.txt 업데이트 및 자동 Git Push
```
---

## 🛠️ 기술 스택 (Tech Stack)
Language: Python 3.10

Libraries: requests, BeautifulSoup4

Automation: GitHub Actions (Workflow, Cron, Secrets)

API: Kakao Developers REST API (OAuth 2.0 Refresh Token Flow)

---

## 📂 프로젝트 구조 (Directory Structure)
```
📦 secure_report
 ┣ 📂 .github
 ┃ ┗ 📂 workflows
 ┃   ┗ 📜 main.yml         # GitHub Actions 자동화 워크플로우 설정
 ┣ 📜 main.py               # 메인 크롤링 및 카카오톡 전송 스크립트
 ┣ 📜 get_token.py          # [초기 세팅] 카카오 리프레시 토큰 발급용 스크립트
 ┣ 📜 kisa_test.py          # [초기 세팅] 단건 크롤링 및 알림 테스트 스크립트
 ┣ 📜 last_kisa_post.txt    # KISA 중복 방지 기록
 ┣ 📜 last_news_post.txt    # 보안뉴스 중복 방지 기록
 ┣ 📜 last_pipc_post.txt    # PIPC 중복 방지 기록
 ┗ 📜 alert_history.txt     # 전체 알림 발송 히스토리 로그
```
---
## 🔧 초기 세팅 및 인증 가이드 (Initial Setup)
1. 카카오 리프레시 토큰 발급 (get_token.py)
   - 카카오톡 API를 통해 '나에게 보내기'를 수행하기 위해 최초 1회 인증 코드를 교환하여 Refresh Token을 발급받는 로컬 테스트용 스크립트입니다.

2. 단건 크롤링 & 알림 테스트 (kisa_test.py)
   - 멀티 소스 확장 전, KISA 가이드라인 크롤링과 카카오톡 전송 기능이 정상 동작하는지 로컬에서 가볍게 검증했던 테스트 스크립트입니다.

---
## 💡 주요 트러블슈팅 및 해결 과정 (Troubleshooting)
Issue 1. 공공기관/보안 사이트 SSL 인증서 검증 에러 (SSL: CERTIFICATE_VERIFY_FAILED)
   - Cause: GitHub Actions(Ubuntu 환경)에서 KISA 등 국내 공공/보안 사이트 접속 시 로컬 인증서 체인 검증에 실패하여 차단되는 현상.

Resolve 1. requests.get() 호출 시 verify=False 옵션을 추가하여 SSL 인증서 검증을 우회하도록 처리.

---

## 🚀 시작하기 (Getting Started)
1. GitHub Secrets 설정
   - 레포지토리의 Settings > Secrets and variables > Actions에 아래 시크릿을 등록합니다.

   - KAKAO_REST_API_KEY: 카카오 디벨로퍼스 REST API 키

   - KAKAO_REFRESH_TOKEN: 카카오 OAuth 2.0 리프레시 토큰

2. 워크플로우 스케줄 (main.yml)
원하는 실행 주기에 맞춰 cron 표현식을 수정하여 사용합니다.
```
YAML
on:
  schedule:
    - cron: '0 22 * * *'    # 한국 시간 오전 7시 00분
    - cron: '30 0 * * *'    # 한국 시간 오전 9시 30분
    - cron: '0 5 * * *'     # 한국 시간 오후 2시 00분
    - cron: '0 8 * * *'     # 한국 시간 오후 5시 00분
  workflow_dispatch:        # 수동 실행 지원
```
---
