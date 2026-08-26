#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export ANDROID_HOME="${ANDROID_HOME:-$HOME/Android/Sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export JAVA_HOME="${JAVA_HOME:-/usr/lib/jvm/java-17-openjdk-amd64}"
export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"

if [[ ! -d "$ANDROID_HOME" ]]; then
  echo "Android SDK not found at $ANDROID_HOME"
  echo "Install Android Studio or set ANDROID_HOME."
  exit 1
fi

if [[ ! -x "$JAVA_HOME/bin/java" ]]; then
  echo "Java 17 not found at $JAVA_HOME"
  echo "Install OpenJDK 17 or set JAVA_HOME."
  exit 1
fi

echo "Using ANDROID_HOME=$ANDROID_HOME"
echo "Using JAVA_HOME=$JAVA_HOME"

npx expo prebuild --platform android

WRAPPER="$ROOT/android/gradle/wrapper/gradle-wrapper.properties"
if [[ -f "$WRAPPER" ]]; then
  sed -i 's/networkTimeout=10000/networkTimeout=120000/' "$WRAPPER"
fi

cd "$ROOT/android"
./gradlew assembleRelease --no-daemon

APK="$ROOT/android/app/build/outputs/apk/release/app-release.apk"
cp "$APK" "$ROOT/lance-on.apk"
echo "APK ready: $ROOT/lance-on.apk"
ls -lh "$ROOT/lance-on.apk"
