# 🛠️ Initial Setup & Local Testing Guide

본 디렉토리는 GitHub Actions 자동화 배포(`main.py`)를 수행하기 전, 카카오 API 인증 토큰을 발급받고 로컬 환경에서 크롤링 및 알림 전송이 정상 동작하는지 검증하기 위한 초기 세팅 스크립트들을 모아둔 공간입니다.

---

## 📂 폴더 구성 (Directory Contents)

* **`get_token.py`**: 카카오 OAuth 2.0 인가 코드를 활용하여 무중단 자동화에 필수적인 **Refresh Token**을 발급받는 스크립트
* **`kisa_test.py`**: 멀티 소스 확장 전, KISA 가이드라인 크롤링과 카카오톡 '나에게 보내기'가 정상 작동하는지 단건으로 테스트하는 스크립트

---

## 🚀 단계별 실행 가이드 (Step-by-Step)

### Step 1. 카카오 리프레시 토큰 발급 (`get_token.py`)

카카오톡 '나에게 보내기' API를 사용하려면 Access Token과 **Refresh Token**이 필요합니다. Access Token은 주기적으로 만료되므로, 갱신용 Refresh Token을 최초 1회 발급받아야 합니다.

1. **카카오 디벨로퍼스 설정**
   * [Kakao Developers](https://developers.kakao.com/) 접속 및 애플리케이션 생성
   * **[카카오 로그인] > [활성화 설정]** 을 `ON`으로 변경
   * **[Redirect URI]** 등록 (예: `https://localhost`)
   * **[동의항목]** 에서 `talk_message` (카카오톡 메시지 전송) 권한을 [사용함]으로 설정

2. **인가 코드(Authorization Code) 발급 받기**
   * 브라우저 주소창에 아래 URL을 조합하여 입력하고 엔터를 누릅니다. (REST_API_KEY와 REDIRECT_URI는 본인 정보로 교체)
     ```text
     [https://kauth.kakao.com/oauth/authorize?client_id=](https://kauth.kakao.com/oauth/authorize?client_id=){YOUR_REST_API_KEY}&redirect_uri={YOUR_REDIRECT_URI}&response_type=code
     ```
   * 로그인 및 동의 후 카카오톡으로 리다이렉트되는 주소(URL) 중 `code=` 뒤에 붙는 긴 문자열을 복사합니다. (이것이 인가 코드입니다.)

3. **`get_token.py` 실행**
   * 스크립트 내부에 `REST_API_KEY`와 복사해 둔 인가 코드를 입력합니다.
   * 터미널에서 실행하여 `refresh_token` 값을 획득하고 안전하게 보관합니다.
     ```bash
     python initial_setup/get_token.py
     ```

---

### Step 2. 단건 크롤링 및 알림 테스트 (`kisa_test.py`)

본격적인 멀티 소스 자동화 봇을 구동하기 전, KISA 가이드라인 파싱과 카카오톡 전송 로직이 에러 없이 깔끔하게 수행되는지 로컬 환경에서 테스트합니다.

1. **환경 변수 또는 코드 내 인증 정보 설정**
   * 발급받은 `KAKAO_REST_API_KEY`와 `KAKAO_REFRESH_TOKEN`이 정상적으로 주입되어 있는지 확인합니다.

2. **테스트 스크립트 실행**
   ```bash
   python initial_setup/kisa_test.py
