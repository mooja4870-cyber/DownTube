#!/bin/zsh
# DownTube 서버 자동 실행 제거
LABEL="com.downtube.server"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

launchctl bootout "gui/$(id -u)/$LABEL" 2>/dev/null || true
rm -f "$PLIST"
echo "자동 실행을 제거했습니다. (수동 실행: ./run.sh --tunnel)"
