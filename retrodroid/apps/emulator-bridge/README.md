# Emulator Bridge

Generic Android bridge app for emulator launches that need app-specific logic between
`ES-DE` and the final emulator activity.

This app is intentionally headless.

- no launcher UI
- no settings UI
- no interactive controls
- behavior changes happen in code, then rebuild/reinstall

This exists for emulators that are not simple "open this ROM file" targets. Typical cases:

- import-based emulators like `RPCSX`
- emulators that expect a game serial / title ID instead of a raw file path
- emulators that need app-private lookup or custom intent extras before launch

## Intended flow

1. `ES-DE` launches this app with:
   - a ROM URI in `%DATA%`
   - an emulator key in `%EXTRA_emulator%`
2. The bridge resolves the target game using emulator-specific logic.
3. The bridge launches the emulator's real activity with the correct action/extras.

## Suggested ES-DE shape

Example command once the app is wired into `es_find_rules.xml`:

```xml
<command label="RPCSX (Bridge)">
    %EMULATOR_EMULATOR-BRIDGE%
    %ACTION%=android.intent.action.VIEW
    %DATA%=%ROMSAF%
    %EXTRA_emulator%=rpcsx
</command>
```

## Current scaffold

The app currently provides:

- an exported, headless `MainActivity`
- a generic request parser
- a handler registry
- an `RPCSX` handler stub
- a `Vita3K` handler stub

It does not yet perform real deep-launch integration.

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











