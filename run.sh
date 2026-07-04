#!/bin/zsh
# DownTube 실행 스크립트
#   ./run.sh            → 로컬(같은 Wi-Fi) 전용 실행
#   ./run.sh --tunnel   → cloudflared 터널로 외부 접속용 공개 URL 발급
set -e
cd "$(dirname "$0")"

# homebrew(cloudflared·ffmpeg)와 node(npx/wrangler) 경로를 명시 — 터미널 외 환경에서도 동작
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
PORT="${DOWNTUBE_PORT:-8756}"

put_kv() {  # KV에 값 기록 (최대 3회 재시도). 성공 시 0 반환
  local key="$1" val="$2" try
  for try in 1 2 3; do
    (cd cloudflare && npx --yes wrangler kv key put "$key" "$val" --binding TUNNEL --remote) \
      >>/tmp/downtube_kv.log 2>&1 && return 0
    sleep 5
  done
  return 1
}

if [[ "$1" == "--tunnel" ]]; then
  : >/tmp/downtube_kv.log
  .venv/bin/uvicorn app:app --host 127.0.0.1 --port "$PORT" &
  SERVER_PID=$!
  LOG=$(mktemp /tmp/downtube_tunnel.XXXXXX)
  cloudflared tunnel --url "http://localhost:$PORT" >"$LOG" 2>&1 &
  CF_PID=$!
  # 종료 시: 서버·터널 중지 + KV 터널 주소 삭제 → 고정 주소가 죽은 터널 대신 "서버 꺼짐" 안내 표시.
  # (동기 삭제 — launchd 자동 재시작 시 새 URL 등록과 경합하지 않도록 종료를 블록)
  cleanup() {
    kill "$SERVER_PID" "$CF_PID" 2>/dev/null
    (cd cloudflare && npx --yes wrangler kv key delete url --binding TUNNEL --remote >/dev/null 2>&1)
  }
  trap cleanup EXIT INT TERM

  echo ""
  echo "고정 주소: https://downtube.mooja4870.workers.dev  ← 핸드폰에는 이 주소만 등록하면 됩니다"
  echo ""
  # 터널 주소 발급을 기다렸다가(최대 90초) Cloudflare KV에 기록 — 메인 흐름에서 처리(백그라운드 서브셸은 launchd에서 불안정)
  URL=""
  for _ in {1..90}; do
    # `|| true` — 아직 URL 미발급 시 grep이 1을 반환해 set -e로 스크립트가 죽는 것을 방지
    URL=$(grep -m1 -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" 2>/dev/null || true)
    [[ -n "$URL" ]] && break
    kill -0 "$CF_PID" 2>/dev/null || break   # 터널이 죽었으면 중단
    sleep 1
  done
  if [[ -n "$URL" ]] && put_kv url "$URL"; then
    echo "터널 연결됨: $URL → 고정 주소에 반영 완료 (반영까지 최대 1분)"
  else
    echo "경고: 고정 주소 갱신 실패(로그: /tmp/downtube_kv.log) — ${URL:-터널 미발급}"
  fi
  wait "$CF_PID"   # 터널이 살아있는 동안 대기; 종료되면 스크립트 종료(→ launchd 재시작)
else
  IP=$(ipconfig getifaddr en0 2>/dev/null || echo "맥IP")
  echo ""
  echo "핸드폰(같은 Wi-Fi)에서 접속: http://$IP:$PORT"
  echo ""
  .venv/bin/uvicorn app:app --host 0.0.0.0 --port "$PORT"
fi
