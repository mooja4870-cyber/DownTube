# Version History

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
