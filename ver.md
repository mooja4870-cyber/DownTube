# Version History

## v3.1.0

Date: 2026-07-03

### 변경 내용

* 접속 비밀번호(로그인) 완전 제거 — 접속하면 바로 탐색 화면 표시
  * 서버: 로그인 API·토큰 인증 코드 제거
  * UI: 로그인 오버레이 제거
  * run.sh: DOWNTUBE_PASSWORD 환경변수 제거
* 주의: 주소를 아는 사람은 누구나 사용 가능하므로 `--tunnel` 사용 시 주소 공유에 유의

### 수정 파일

* app.py (인증 코드 제거)
* static/index.html (로그인 UI 제거)
* run.sh, README.md (비밀번호 안내 제거)

### 검증 내용

* 비밀번호·쿠키 없이 메인 화면, 검색 API, 작업 목록 API 정상 응답 확인
* 모바일 뷰포트 브라우저에서 로그인 화면 없이 바로 피드 로딩 확인 (콘솔 오류 없음)

## v3.0.1

Date: 2026-07-03

### 변경 내용

* 버그 수정: `static/index.html`을 서버를 거치지 않고 직접(파일/미리보기 패널) 열었을 때
  `Failed to parse URL from /api/search...` 오류 발생 → http(s) 접속이 아니면
  "run.sh 실행 후 표시되는 서버 주소로 접속해 주세요" 안내 메시지를 표시하도록 개선
* 서버 주소로 접속하는 정상 사용에는 영향 없음 (스포츠 카테고리 피드 로딩 재검증 완료)

### 수정 파일

* static/index.html (api() 함수에 접속 방식 가드 추가)

## v3.0.0

Date: 2026-07-03

### 변경 내용

* **유튜브식 탐색 UI로 전면 개편** — URL 입력 방식 완전 제거
  * 홈 피드: 카테고리 탭(인기·음악·뉴스·예능·스포츠·게임·영화·먹방·여행·키즈)별 인기 영상 그리드
  * 키워드 검색: 검색창 입력 → 썸네일·제목·채널·재생시간·조회수 카드 목록 ("더 보기"로 추가 로드)
  * 영상 카드 탭 → 하단 시트: 유튜브 임베드 미리보기(▶), MP4 화질/MP3 선택 → 다운로드
  * 하단 내비게이션(탐색/다운로드) + 진행 중 작업 배지
* 백엔드: `/api/search` 신설 (yt-dlp ytsearch, 10분 캐시), 다운로드는 영상 ID 기반으로 변경
* `.claude/launch.json` 추가 (미리보기 실행 설정)

### 수정 파일

* app.py (검색 API 추가, URL 입력 제거, ID 기반 다운로드로 재작성)
* static/index.html (탐색/검색/바텀시트 UI로 전면 재작성)
* README.md (사용법 갱신)
* .claude/launch.json (신규)

### 검증 내용

* 키워드 검색 API(제목·채널·재생시간·조회수 반환) 및 미인증 401 차단 확인
* 모바일 뷰포트(375×812)에서 피드 로딩, 카테고리 칩, 카드 탭 → 바텀시트, 검색 → 결과 선택 → MP3 다운로드 → 다운로드 탭 완료 표시까지 전체 흐름 실제 브라우저로 확인

## v2.0.0

Date: 2026-07-03

### 변경 내용

* **DownTube 앱 신규 개발** — 유튜브 영상·재생목록·채널을 MP4/MP3로 다운로드하는 모바일용 웹 앱
  * FastAPI + yt-dlp + ffmpeg 기반 서버 (`app.py`)
  * 모바일 최적화 웹 UI (`static/index.html`) — URL 입력, MP4 화질 선택(최고/1080p/720p/480p), MP3 변환, 진행률 표시, 파일별 저장 및 전체 ZIP 저장
  * 재생목록·채널 URL 입력 시 포함된 모든 영상 일괄 다운로드
  * 비밀번호 인증 (기본 `downtube1234`, `DOWNTUBE_PASSWORD` 환경변수로 변경)
  * 실행 스크립트 `run.sh` — 로컬(같은 Wi-Fi) 모드 / `--tunnel` 외부 접속 모드(cloudflared 공개 URL)
* 이전 PnL 분석 스크립트(analyze_pnl.py, compare_configs.py) 제거 — v1.0.0 태그에서 복구 가능

### 수정 파일

* app.py (신규)
* static/index.html (신규)
* run.sh (신규)
* README.md (신규)
* .gitignore (신규)
* analyze_pnl.py, compare_configs.py (삭제)

### 검증 내용

* 단일 영상 MP4(720p/480p) 및 MP3(192kbps) 다운로드 정상 확인
* 채널 URL(@jawed/videos) 전체 영상 다운로드 정상 확인
* ZIP 일괄 다운로드, 비밀번호 인증(미인증 401 차단) 정상 확인
* cloudflared 터널 외부 접속(trycloudflare.com) 정상 확인

## v1.0.0

Date: 2026-05-31

### 변경 내용

* 프로젝트 초기 커밋 (analyze_pnl.py, compare_configs.py)
* VS Code Python 인터프리터 경로 오류 근본 해결
  * `.vscode/settings.json` 생성 — `python.defaultInterpreterPath`를 시스템 `python3`으로 설정
  * Antigravity IDE 글로벌 User Settings에 `python.defaultInterpreterPath: python3` 추가

### 수정 파일

* .vscode/settings.json (신규)
* /Users/l/Library/Application Support/Antigravity IDE/User/settings.json (글로벌 설정)
