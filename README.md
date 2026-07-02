# DownTube

유튜브 영상·재생목록·채널을 MP4(화질 선택) 또는 MP3로 다운로드하는 개인용 웹 앱.
핸드폰 브라우저에서 접속해 파일을 핸드폰에 직접 저장할 수 있다.

## 실행

```bash
./run.sh            # 같은 Wi-Fi 전용 — 터미널에 표시되는 http://맥IP:8756 로 접속
./run.sh --tunnel   # 외부 접속용 — 표시되는 https://xxxx.trycloudflare.com 로 접속
```

- 접속 비밀번호 기본값: `downtube1234` — 변경하려면 `DOWNTUBE_PASSWORD=새비번 ./run.sh --tunnel`
- 포트 변경: `DOWNTUBE_PORT=포트번호`

## 사용법 (핸드폰)

1. 브라우저로 위 주소 접속 → 비밀번호 입력
2. 유튜브 URL 붙여넣기 (영상 하나 / 재생목록 / 채널 URL 모두 가능)
3. MP4(최고화질·1080p·720p·480p) 또는 MP3 선택 → 다운로드
4. 완료되면 파일별 링크 또는 "전체 ZIP으로 받기"를 눌러 핸드폰에 저장

## 구성

- `app.py` — FastAPI 서버 (yt-dlp + ffmpeg)
- `static/index.html` — 모바일 웹 UI
- `run.sh` — 실행 스크립트 (로컬 / cloudflared 터널)
- `downloads/` — 서버 측 임시 저장 폴더 (작업 삭제 시 함께 삭제)

## 주의

본인 소유 영상 또는 개인적 이용 범위 내에서만 사용할 것.
