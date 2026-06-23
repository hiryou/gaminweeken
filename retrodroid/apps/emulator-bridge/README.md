# Emulator Bridge

Generic Android bridge app for launches that need app-specific logic between
`ES-DE` and the final target app.

This app is intentionally headless.

- no launcher UI
- no settings UI
- no interactive controls
- behavior changes happen in code, then rebuild/reinstall

This exists for targets that are not simple "open this file in the final app" cases.

Current use:

- `ports-apk`
  - inspect a selected `.apk`
  - read its package name from the APK manifest
  - if already installed, launch the installed app
  - otherwise hand off to the Android package installer

## Intended flow

1. `ES-DE` launches this app with:
   - a ROM URI in `%DATA%`
   - an emulator key in `%EXTRA_emulator%`
2. The bridge resolves the selected target using app-specific logic.
3. The bridge either launches the installed app or starts the Android installer flow.

## Suggested ES-DE shape

Example command once the app is wired into `es_find_rules.xml`:

```xml
<command label="Android APK (Bridge)">
    %EMULATOR_EMULATOR-BRIDGE%
    %ACTION%=android.intent.action.VIEW
    %DATA%=%ROMSAF%
    %EXTRA_emulator%=ports-apk
</command>
```

## Current behavior

The app currently supports:

- an exported, headless `MainActivity`
- a generic request parser
- a `ports-apk` bridge path

It does not include the old RPCSX/Vita bridge experiments anymore.

## Dev getting started

Generate wrapper files in this root directory:
```shell
$ gradle wrapper --gradle-version 9.4.1
```

After that, stop using system Gradle and use:
```shell
$ ./gradlew tasks
```

Set content in local.properties e.g.
```text
sdk.dir=/opt/homebrew/share/android-commandlinetools
```

Install SDK API 37
```shell
$ sdkmanager --sdk_root="$ANDROID_HOME" \
    "platform-tools" \
    "platforms;android-37.0" \
    "build-tools;37.0.0"
# and accept the prompted terms & conditions
# ...
# January 16, 2019
# ---------------------------------------
# Accept? (y/N): y
# [=======================================] 100% Unzipping... platform-tools/NOTIC
```

Accept all pending SDK licenses:
```shell
$ sdkmanager --sdk_root="$ANDROID_HOME" --licenses
# ...
# ---------------------------------------
# Accept? (y/N): y
# All SDK package licenses accepted
```

Lastly, build the .apk
```shell
$ ./gradlew assembleDebug
```

After droid_setup i.e. installation of all apks, check if this app was installed:
```shell
$ adb -s "$DROID_ADB_SERIAL" shell pm list packages | grep io.retrodroid.emulatorbridge
package:io.retrodroid.emulatorbridge
```










