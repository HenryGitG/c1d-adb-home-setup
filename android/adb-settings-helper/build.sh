#!/usr/bin/env bash
set -euo pipefail

project_dir="$(cd "$(dirname "$0")" && pwd)"
sdk_dir="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
tools_dir="$sdk_dir/build-tools/36.0.0"
platform_jar="$sdk_dir/platforms/android-36/android.jar"
build_dir="$project_dir/build"
output_apk="$project_dir/dist/C1D-ADB-Settings-Helper.apk"

mkdir -p "$build_dir/classes" "$project_dir/dist"
"$tools_dir/aapt2" compile --dir "$project_dir/res" -o "$build_dir/resources.zip"
"$tools_dir/aapt2" link -o "$build_dir/unsigned.apk" \
    --manifest "$project_dir/AndroidManifest.xml" -I "$platform_jar" \
    "$build_dir/resources.zip"
javac --release 8 -Xlint:-options -encoding UTF-8 -cp "$platform_jar" \
    -d "$build_dir/classes" \
    "$project_dir/src/com/henry/c1d/devsettings/MainActivity.java"
"$tools_dir/d8" --min-api 21 --lib "$platform_jar" --output "$build_dir" \
    "$build_dir/classes/com/henry/c1d/devsettings/MainActivity.class"
cp "$build_dir/unsigned.apk" "$build_dir/with-code.apk"
zip -q -j "$build_dir/with-code.apk" "$build_dir/classes.dex"
"$tools_dir/zipalign" -f 4 "$build_dir/with-code.apk" "$build_dir/aligned.apk"
"$tools_dir/apksigner" sign \
    --ks "$HOME/.android/debug.keystore" \
    --ks-key-alias androiddebugkey \
    --ks-pass pass:android \
    --key-pass pass:android \
    --out "$output_apk" "$build_dir/aligned.apk"
"$tools_dir/apksigner" verify "$output_apk"
echo "$output_apk"
