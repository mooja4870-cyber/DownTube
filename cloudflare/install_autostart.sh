#!/bin/zsh
# DownTube 서버 자동 실행 설치 (macOS LaunchAgent)
#   Mac 로그인 시 서버+터널이 자동으로 켜지고, 꺼지면 자동 재시작하며 고정 주소(KV)를 갱신한다.
set -e
cd "$(dirname "$0")/.."          # 프로젝트 루트
PROJECT_DIR="$(pwd)"
RUN_SH="$PROJECT_DIR/run.sh"
LABEL="com.downtube.server"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$HOME/Library/LaunchAgents"
# 템플릿의 경로 자리표시자를 실제 경로로 치환
sed -e "s|__RUN_SH__|$RUN_SH|g" -e "s|__PROJECT_DIR__|$PROJECT_DIR|g" \
  cloudflare/com.downtube.server.plist > "$PLIST"

# 기존 등록이 있으면 내리고 다시 올림
launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST"
launchctl enable "gui/$(id -u)/$LABEL"

echo "설치 완료: $PLIST"
echo "로그: tail -f /tmp/downtube.out /tmp/downtube.err"
echo "제거: ./cloudflare/uninstall_autostart.sh"
