# Version History

## v3.6.0

Date: 2026-07-04

### 변경 내용

* **클라우드 VM(도커) 배포 패키지 추가** — Mac을 꺼도 24시간 작동
  * `vm/Dockerfile`·`docker-compose.yml`·`entrypoint.sh`·`requirements.txt` — 어느 클라우드 VM(x86/ARM)에서든 `docker compose up -d` 한 번으로 배포
  * `vm/update_kv.py` — node/wrangler 없이 Cloudflare REST API로 고정 주소(KV) 갱신(토큰 사용)
  * `vm/DEPLOY.md` — VM 준비·토큰 발급·실행 단계별 안내
* 컨테이너는 앱 + cloudflared 터널 + KV 자동 갱신을 함께 실행, 기존 고정 주소/앱 그대로 사용

### 한계 (정직한 고지)

* **Cloudflare Workers 자체로는 실행 불가** — Python/yt-dlp/ffmpeg를 못 돌리므로, 실제 다운로드는 VM에서 수행하고 Worker는 고정 주소 중계만 담당
* **유튜브의 클라우드 IP 차단** 가능성 — 봇 감지로 다운로드가 막힐 수 있으며, 이 경우 쿠키 전달 또는 가정용 IP 방식이 필요 (DEPLOY.md 참고)

### 수정 파일

* vm/** (신규), README.md (vm/ 안내)

### 검증 내용

* 컨테이너와 동일한 파일 레이아웃으로 entrypoint 실행 → 서버 200, 검색 API 정상, cloudflared 터널 발급, update_kv.py 요청 정상(더미 토큰 401 확인 = 요청 구조 정상, 실토큰이면 성공) 로컬 검증
* (Docker 데몬은 로컬에 없어 이미지 빌드 자체는 VM에서 최초 1회 검증 필요)

## v3.5.0

Date: 2026-07-04

### 변경 내용

* **Mac 서버 자동 실행 (macOS LaunchAgent)** — 매번 수동으로 켜야 하던 번거로움 해소
  * `cloudflare/install_autostart.sh` / `uninstall_autostart.sh` / `com.downtube.server.plist`
  * 로그인 시 서버+터널 자동 시작, 종료·크래시 시 자동 재시작(KeepAlive), 고정 주소(KV) 자동 갱신
* **run.sh 견고성 수정** (자동 실행이 실패하던 근본 원인 해결)
  * `set -e` 상태에서 `URL=$(grep …)`가 URL 미발급 순간 grep 실패로 스크립트가 즉시 종료되던 버그 → `|| true`로 방지
  * KV 갱신을 백그라운드 서브셸에서 메인 흐름으로 이동 (launchd에서 서브셸이 불안정하던 문제 해결)
  * cloudflared를 백그라운드로 돌리고 `wait`로 대기, 종료 시 KV 삭제(동기)

### 수정 파일

* run.sh (KV 갱신 로직 재작성, set -e 버그 수정)
* cloudflare/com.downtube.server.plist, install_autostart.sh, uninstall_autostart.sh (신규)
* README.md (자동 실행 안내)

### 검증 내용

* 수동 실행·launchd 실행 양쪽에서 서버 기동 → 터널 연결 → KV 갱신("반영 완료") 확인
* launchd: state=running, keepalive·runatload 적용, 고정 주소 → 현재 터널 → 앱/검색 API 200 전체 확인

## v3.4.5

Date: 2026-07-04

### 변경 내용

* run.sh 종료 시 KV의 터널 주소를 삭제하도록 개선
  * 이전: 서버를 끄면 고정 주소가 이미 죽은 옛 터널로 리다이렉트 → 앱에서 `ERR_NAME_NOT_RESOLVED`(찾을 수 없음)
  * 개선: 종료 시 KV 키 삭제 → 고정 주소가 깔끔한 "서버가 꺼져 있습니다" 안내(503) 표시
* (운영) 꺼져 있던 Mac 서버·터널을 재기동하고 고정 주소(KV)를 현재 터널로 갱신하여 즉시 정상화

### 수정 파일

* run.sh (종료 시 KV 정리)

### 검증 내용

* 서버·터널 재기동 후 고정 주소 → 302 → 터널 → 앱/검색 API 200 정상 확인

## v3.4.4

Date: 2026-07-04

### 변경 내용

* **APK에서 삭제가 되지 않던 버그 수정**
  * 원인: 앱 WebView에 `WebChromeClient`가 없어 JS `confirm()`(삭제 확인창)이 무조건 '취소'로 처리 → 다중 선택 삭제가 조용히 중단됨 (웹브라우저·개별 삭제는 정상이라 놓쳤던 문제)
  * 수정: `web.setWebChromeClient(new WebChromeClient())` 추가 — confirm/alert 등 JS 다이얼로그 정상 동작
* APK 버전 3.4.4(344)

### 수정 파일

* android/java/com/downtube/app/MainActivity.java (WebChromeClient 추가)
* android/AndroidManifest.xml (버전), DownTube.apk (재빌드)

### 검증 내용 (Android 14 에뮬레이터, 앱 → 실서버 직결)

* 다중 선택 삭제: "삭제 (2)" → 확인창 정상 표시 → OK → 2개 작업 삭제(서버 0) 확인
* 개별 삭제 버튼: 작업 삭제(서버 0) 확인
* 첫 실행 자동 접속 및 접속 실패 시 주소 입력창 동작 확인

## v3.4.3

Date: 2026-07-03

### 변경 내용

* **APK 첫 실행 시 서버 주소 자동 접속** — 매번 주소를 입력해야 하던 불편 해소
  * 기본 접속 주소를 고정 Cloudflare 주소(https://downtube.mooja4870.workers.dev)로 내장
  * 저장된 주소가 없으면 곧바로 기본 주소에 접속 (입력 대화상자 생략)
  * 주소 변경이 필요하면 첫 화면에서 뒤로가기 → 입력창(기본 주소 미리 채워짐)
* APK 버전 3.4.3(343)

### 수정 파일

* android/java/com/downtube/app/MainActivity.java (DEFAULT_BASE 자동 접속)
* android/AndroidManifest.xml (버전), DownTube.apk (재빌드)
* README.md (자동 접속 안내)

### 검증 내용

* 에뮬레이터에 신규 설치 후 실행 → 주소 입력창 없이 피드 자동 로딩 확인

## v3.4.2

Date: 2026-07-03

### 변경 내용

* **APK 저장 파일 확장자 버그 수정** — 안드로이드 에뮬레이터(Android 14)에서 설치→접속→검색→다운로드 전 과정을 실기기 수준으로 검증하던 중 발견
  * 증상: 핸드폰에 저장된 파일이 `.mp3`/`.mp4` 대신 `.bin` 확장자로 저장되어 재생 불가
  * 원인: 서버가 파일을 `application/octet-stream`으로 보내면 안드로이드 `URLUtil.guessFileName`이 확장자를 `.bin`으로 치환
  * 앱: Content-Disposition/URL에서 파일명을 직접 추출하도록 수정 (구버전 서버와도 호환)
  * 서버: 파일 MIME 타입을 확장자 기반(audio/mpeg, video/mp4 등)으로 정확히 전송
* APK 버전 3.4.2(342)

### 수정 파일

* android/java/com/downtube/app/MainActivity.java (파일명 추출 로직)
* app.py (MIME 타입 수정)
* android/AndroidManifest.xml (버전), DownTube.apk (재빌드)

### 검증 내용 (Android 14 에뮬레이터, 실제 서버·고정 주소 경유)

* APK 설치 Success, 실행·크래시 없음, 서버 주소 입력 → 고정 주소 접속 → 피드/검색 정상
* 영상 선택 → MP3 다운로드 → 파일 링크 탭 → 핸드폰 Download 폴더에 `.mp3` 확장자로 저장 확인 (유효한 MPEG 오디오)
* apksigner 서명(v2+v3)·zipalign·리소스 비압축 검증 통과

## v3.4.1

Date: 2026-07-03

### 변경 내용

* 버그 수정: `run.sh --tunnel` 실행 시 고정 주소(KV) 갱신이 조용히 실패하던 문제
  * 원인: run.sh의 PATH에 node/npx 경로(/usr/local/bin)가 없어 터미널 외 환경에서 wrangler 실행 실패
  * PATH에 /usr/local/bin 추가, KV 갱신 3회 재시도, 실패 로그를 /tmp/downtube_kv.log에 기록
* 실행 중이던 터널 주소를 KV에 수동 반영하여 고정 주소 즉시 정상화

### 수정 파일

* run.sh (PATH 보강, KV 갱신 재시도·로그)

### 검증 내용

* 고정 주소 → 302 → 실행 중 터널 → 앱 200 및 검색 API 정상 확인

## v3.4.0

Date: 2026-07-03

### 변경 내용

* **Cloudflare 배포(wrangler)** — 고정 접속 주소 제공
  * Worker `downtube` 배포: **https://downtube.mooja4870.workers.dev**
  * 매번 바뀌던 trycloudflare 터널 주소를 KV에 저장하고, 고정 주소 접속 시 현재 터널로 302 리다이렉트
  * 서버(터널)가 꺼져 있으면 고정 주소에서 실행 안내 문구 표시(503)
  * `run.sh --tunnel`: 터널 주소 발급 시 KV 자동 갱신 로직 추가 — 핸드폰/APK에는 고정 주소 한 번만 등록하면 됨
* 참고: 앱 본체(Python+yt-dlp+ffmpeg)는 Workers 실행 환경 특성상 Cloudflare에 올릴 수 없어
  Mac 서버 + 고정 주소 Worker 구조로 배포함

### 수정 파일

* cloudflare/worker.js, cloudflare/wrangler.toml (신규)
* run.sh (KV 자동 갱신)
* README.md (고정 주소 안내)

### 검증 내용

* 고정 주소 → 302 → 터널 → 앱 HTML/검색 API 200 전체 체인 확인
* 서버 꺼짐 상태에서 고정 주소 503 안내 문구 확인
* KV 갱신 반영(전파 지연 약 1분 이내) 확인

## v3.3.1

Date: 2026-07-03

### 변경 내용

* **앱 아이콘 추가** — 빨간 그라데이션 배경에 흰색 재생▶ + 다운로드↓ 글리프
  * 어댑티브 아이콘(Android 8.0+, 런처 모양에 맞게 자동 마스킹) + 레거시 아이콘(둥근 모서리) 모두 포함
  * 전 해상도(mdpi~xxxhdpi) PNG 생성 스크립트 `android/make_icons.py` (Pillow)
* APK 버전 3.3.1(331)로 갱신, 크기 약 50KB

### 수정 파일

* android/make_icons.py, android/res/** (신규)
* android/AndroidManifest.xml (아이콘 연결, 버전 갱신)
* android/build_apk.sh (리소스 컴파일 단계 추가)
* DownTube.apk (재빌드)

### 검증 내용

* aapt2 badging에서 어댑티브 아이콘 연결 확인, apksigner 서명 검증 통과
* GitHub raw 링크에서 새 APK 다운로드 및 로컬 파일 일치 확인

## v3.3.0

Date: 2026-07-03

### 변경 내용

* GitHub 저장소 연결 및 푸시 — https://github.com/mooja4870-cyber/DownTube (main·master 브랜치, 전체 태그)
* **안드로이드 APK 추가** (`DownTube.apk`, 약 12KB)
  * WebView 기반 네이티브 앱 — 실행 시 서버 주소 입력(저장됨), 뒤로가기로 주소 변경
  * 파일 다운로드는 안드로이드 DownloadManager로 핸드폰 '다운로드' 폴더에 저장
  * minSdk 24(Android 7.0+), targetSdk 34, 디버그 키 서명
  * 다운로드 링크: https://github.com/mooja4870-cyber/DownTube/raw/master/DownTube.apk
* 빌드 스크립트 `android/build_apk.sh` (Gradle 없이 aapt2+javac+d8+apksigner 사용)

### 수정 파일

* android/AndroidManifest.xml, android/java/com/downtube/app/MainActivity.java, android/build_apk.sh (신규)
* DownTube.apk (신규, 빌드 산출물)
* README.md (APK 설치 안내 추가)

### 검증 내용

* apksigner 서명 검증, aapt2 badging(패키지명·권한·런처 액티비티) 확인
* GitHub main/master 푸시 및 태그 업로드 확인

## v3.2.0

Date: 2026-07-03

### 변경 내용

* 다운로드 탭 **다중 선택 기능** 추가
  * '선택' 버튼 → 체크박스 선택 모드, '전체선택/전체해제' 지원
  * **받기 (n)**: 선택한 영상 파일들을 순차적으로 핸드폰에 저장 (브라우저의 다중 다운로드 허용 필요)
  * **ZIP**: 선택한 작업들의 파일을 하나의 ZIP으로 묶어 저장 (`/api/zip?ids=...` 신설, 파일명 중복 자동 처리)
  * **삭제 (n)**: 선택한 작업들 일괄 삭제 (확인 대화상자 후 진행)
  * 기존 개별 저장·개별 삭제는 그대로 유지
* 서버 재시작 시 이전 세션의 잔여 다운로드 파일 자동 정리 (작업 목록이 메모리 기반이라 재시작 후 접근 불가한 파일이 쌓이던 문제)

### 수정 파일

* app.py (다중 ZIP API, 시작 시 잔여 파일 정리)
* static/index.html (선택 모드 UI, 하단 액션 바)

### 검증 내용

* 2개 작업 생성 → 선택 모드 → 전체선택(받기/삭제 버튼 카운트 표시) → 다중 ZIP(두 파일 포함 확인) → 다중 삭제(서버 파일까지 제거) 전체 흐름 확인
* 서버 재시작 시 잔여 폴더 정리 동작 확인

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
