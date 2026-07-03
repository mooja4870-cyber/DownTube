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
  LOG=$(mktemp /tmp/downtube_tunnel.XXXXXX)
  echo ""
  echo "고정 주소: https://downtube.mooja4870.workers.dev  ← 핸드폰에는 이 주소만 등록하면 됩니다"
  echo ""
  # 터널 주소가 발급되면 Cloudflare KV에 기록해 고정 주소가 항상 최신 터널을 가리키게 함
  (
    for _ in {1..60}; do
      URL=$(grep -m1 -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" 2>/dev/null)
      if [[ -n "$URL" ]]; then
        if (cd cloudflare && npx --yes wrangler kv key put url "$URL" --binding TUNNEL --remote >/dev/null 2>&1); then
          echo "터널 연결됨: $URL → 고정 주소에 반영 완료"
        else
          echo "경고: 고정 주소 갱신 실패 — $URL 로 직접 접속하세요"
        fi
        break
      fi
      sleep 1
    done
  ) &
  cloudflared tunnel --url "http://localhost:$PORT" 2>&1 | tee "$LOG"
else
  IP=$(ipconfig getifaddr en0 2>/dev/null || echo "맥IP")
  echo ""
  echo "핸드폰(같은 Wi-Fi)에서 접속: http://$IP:$PORT"
  echo ""
  .venv/bin/uvicorn app:app --host 0.0.0.0 --port "$PORT"
fi
