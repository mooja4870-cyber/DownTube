#!/bin/zsh
# DownTube 실행 스크립트
#   ./run.sh            → 로컬(같은 Wi-Fi) 전용 실행
#   ./run.sh --tunnel   → cloudflared 터널로 외부 접속용 공개 URL 발급
set -e
cd "$(dirname "$0")"

export PATH="/opt/homebrew/bin:$PATH"
PORT="${DOWNTUBE_PORT:-8756}"

if [[ "$1" == "--tunnel" ]]; then
  .venv/bin/uvicorn app:app --host 127.0.0.1 --port "$PORT" &
  SERVER_PID=$!
  trap 'kill $SERVER_PID 2>/dev/null' EXIT INT TERM
  echo ""
  echo "잠시 후 출력되는 https://xxxx.trycloudflare.com 주소로 핸드폰에서 접속하세요."
  echo ""
  cloudflared tunnel --url "http://localhost:$PORT"
else
  IP=$(ipconfig getifaddr en0 2>/dev/null || echo "맥IP")
  echo ""
  echo "핸드폰(같은 Wi-Fi)에서 접속: http://$IP:$PORT"
  echo ""
  .venv/bin/uvicorn app:app --host 0.0.0.0 --port "$PORT"
fi
