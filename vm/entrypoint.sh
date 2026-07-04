#!/usr/bin/env bash
# 컨테이너 시작: 서버 + cloudflared 터널 + 고정 주소(KV) 갱신
set -u
PORT="${DOWNTUBE_PORT:-8756}"
LOG=/tmp/cf.log

uvicorn app:app --host 127.0.0.1 --port "$PORT" &
SERVER_PID=$!

cloudflared tunnel --url "http://localhost:$PORT" >"$LOG" 2>&1 &
CF_PID=$!

cleanup() {
  kill "$SERVER_PID" "$CF_PID" 2>/dev/null
  python update_kv.py delete >/dev/null 2>&1 || true   # 종료 시 고정 주소가 죽은 터널 대신 "서버 꺼짐" 안내를 표시
}
trap cleanup EXIT INT TERM

echo "고정 주소: https://downtube.mooja4870.workers.dev"
URL=""
for _ in $(seq 1 90); do
  URL=$(grep -m1 -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG" 2>/dev/null || true)
  [ -n "$URL" ] && break
  kill -0 "$CF_PID" 2>/dev/null || break
  sleep 1
done

if [ -n "$URL" ]; then
  if python update_kv.py put "$URL"; then
    echo "터널 연결됨: $URL → 고정 주소에 반영 완료"
  else
    echo "경고: 고정 주소(KV) 갱신 실패 — CF_API_TOKEN 을 확인하세요. 직접 접속: $URL"
  fi
else
  echo "경고: 터널 주소를 발급받지 못했습니다."
fi

wait "$CF_PID"   # 터널이 살아있는 동안 대기; 종료되면 컨테이너 종료(→ restart 정책으로 재시작)
