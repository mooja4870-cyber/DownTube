# DownTube

유튜브를 둘러보듯 영상을 탐색·검색하고, 선택한 영상을 MP4(화질 선택) 또는 MP3로
다운로드하는 개인용 웹 앱. 핸드폰 브라우저에서 접속해 파일을 핸드폰에 직접 저장한다.

## 실행

```bash
./run.sh            # 같은 Wi-Fi 전용 — 터미널에 표시되는 http://맥IP:8756 로 접속
./run.sh --tunnel   # 외부 접속용 — 고정 주소 https://downtube.mooja4870.workers.dev 로 접속
```

- **고정 주소**: `--tunnel`로 실행하면 매번 바뀌는 터널 주소가 Cloudflare Worker(KV)에 자동 반영되어,
  핸드폰에는 고정 주소 하나만 등록하면 된다. 서버가 꺼져 있으면 고정 주소가 안내 문구를 보여준다.
- Worker 배포/수정: `cd cloudflare && npx wrangler deploy` (wrangler 로그인 필요)
- 포트 변경: `DOWNTUBE_PORT=포트번호`

### 자동 실행 (Mac 로그인 시 항상 켜짐)

```bash
./cloudflare/install_autostart.sh     # 설치 — 로그인 시 서버+터널 자동 시작, 꺼지면 자동 재시작
./cloudflare/uninstall_autostart.sh   # 제거
tail -f /tmp/downtube.out             # 상태/로그 확인
```

- macOS LaunchAgent(`com.downtube.server`)로 등록되어, 서버·터널이 죽으면 자동 재시작하고 고정 주소(KV)를 갱신한다.
- 단, **Mac이 켜져 있어야** 하며 절전(잠자기) 상태에서는 외부 접속이 끊긴다(깨어나면 자동 복구).
- 접속 비밀번호 없음 — 주소를 아는 사람은 누구나 사용 가능 (특히 `--tunnel` 사용 시 주의)

## 안드로이드 앱 (APK)

**다운로드**: <https://github.com/mooja4870-cyber/DownTube/raw/master/DownTube.apk>

1. 핸드폰에서 위 링크로 APK 다운로드 → 설치 (설정에서 '출처를 알 수 없는 앱 허용' 필요)
2. 앱 실행 → **고정 주소로 자동 접속** (주소 입력 불필요)
   - 단, Mac에서 `./run.sh --tunnel` 이 실행 중이어야 화면이 뜬다. 꺼져 있으면 안내 문구가 표시됨
3. 이후 웹과 동일하게 사용 — 파일은 핸드폰 '다운로드' 폴더에 저장됨
4. 서버 주소 변경(예: 같은 Wi-Fi 직접 접속 `http://맥IP:8756`): 첫 화면에서 뒤로가기 버튼 → 주소 입력창

APK 다시 빌드: `./android/build_apk.sh` (Android SDK build-tools 필요)

## 사용법 (핸드폰)

1. 브라우저로 위 주소 접속
2. **탐색**: 카테고리 탭(인기·음악·뉴스·예능·스포츠·게임·영화·먹방·여행·키즈)별 인기 영상을 둘러보거나, 검색창에 키워드 입력
3. 영상 카드를 누르면 하단 시트가 열림 — ▶ 버튼으로 미리보기 가능
4. MP4(최고화질·1080p·720p·480p) 또는 MP3 선택 → 다운로드
5. 하단 **다운로드** 탭에서 진행률 확인, 완료된 파일을 누르면 핸드폰에 저장

## 구성

- `app.py` — FastAPI 서버 (yt-dlp 검색 + 다운로드, ffmpeg 변환)
- `static/index.html` — 모바일 웹 UI (탐색/검색/바텀시트/다운로드 탭)
- `run.sh` — 실행 스크립트 (로컬 / cloudflared 터널 + 고정 주소 자동 갱신)
- `cloudflare/` — 고정 주소 Worker (wrangler로 배포, KV에 현재 터널 주소 저장)
- `android/` — 안드로이드 WebView 앱 소스 및 빌드 스크립트
- `downloads/` — 서버 측 임시 저장 폴더 (작업 삭제 시 함께 삭제)

## 주의

본인 소유 영상 또는 개인적 이용 범위 내에서만 사용할 것.
