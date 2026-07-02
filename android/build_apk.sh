#!/bin/zsh
# DownTube.apk 빌드 스크립트 (Gradle 없이 SDK 도구만 사용)
# 산출물: 저장소 루트의 DownTube.apk
set -e
cd "$(dirname "$0")"

SDK="$HOME/Library/Android/sdk"
BT="$SDK/build-tools/34.0.0"
PLATFORM="$SDK/platforms/android-36/android.jar"
KS="$HOME/.android/debug.keystore"
OUT=build

rm -rf "$OUT" && mkdir -p "$OUT/classes"

# 디버그 서명 키가 없으면 생성
if [[ ! -f "$KS" ]]; then
  mkdir -p "$HOME/.android"
  keytool -genkeypair -keystore "$KS" -storepass android -keypass android \
    -alias androiddebugkey -keyalg RSA -keysize 2048 -validity 10000 \
    -dname "CN=Android Debug,O=Android,C=US"
fi

# 1) 매니페스트 → 리소스 없는 기본 APK
"$BT/aapt2" link -o "$OUT/base.apk" --manifest AndroidManifest.xml -I "$PLATFORM" \
  --min-sdk-version 24 --target-sdk-version 34

# 2) 자바 컴파일 → DEX 변환
javac -d "$OUT/classes" -classpath "$PLATFORM" -source 11 -target 11 \
  java/com/downtube/app/MainActivity.java
"$BT/d8" --release --min-api 24 --lib "$PLATFORM" --output "$OUT" \
  "$OUT"/classes/com/downtube/app/*.class

# 3) DEX 패키징 → 정렬 → 서명
(cd "$OUT" && zip -q base.apk classes.dex)
"$BT/zipalign" -f 4 "$OUT/base.apk" "$OUT/aligned.apk"
"$BT/apksigner" sign --ks "$KS" --ks-pass pass:android --key-pass pass:android \
  --out ../DownTube.apk "$OUT/aligned.apk"

echo "빌드 완료: $(cd .. && pwd)/DownTube.apk"
