# RPCSX Fat Princess Mali Crash Handoff

## Scope

This handoff is for continuing the Android crash investigation around `Fat Princess` in RPCSX.

The active codebase for the emulator work is:

- `/Users/longn/github/forks/rpcsx`

This `retrodroid` repo is not the code being modified for the crash itself. This file exists here only as an agent handoff record.

## User Goal

Understand where, why, and how `Fat Princess` crashes on the Android device when running RPCSX, then either:

- implement a feasible fix, or
- conclude honestly that the issue is outside a practical RPCSX-side fix

The current direction is to dump the exact crashing Vulkan shader/pipeline state and try a narrow Mali-specific workaround.

## Device / Environment

- Android target via `adb`: `192.168.0.99:5555`
- Local Mac is the `adb` control machine
- Remote build machine: `ctower`
- Builds on `ctower` must follow the `ctower-build` skill and happen inside Docker, not on the bare host
- Docker spec used for local publishing of the RPCSX Android core:
  - `/Users/longn/github/forks/rpcsx/_builder/docker-compose.yml`

Important operational constraint:

- Build on `ctower`
- Copy the produced `librpcsx.so` back to this Mac
- Install/test from this Mac via `adb`

## Controller Input

Do not improvise the controller action.

The user explicitly said to use the exact known-good event sequence that reproduces the `A` press:

```text
/dev/input/event5: 0004 0004 00090001
/dev/input/event5: 0001 0130 00000001
/dev/input/event5: 0000 0000 00000000
/dev/input/event5: 0004 0004 00090001
/dev/input/event5: 0001 0130 00000000
/dev/input/event5: 0000 0000 00000000
```

The user was very explicit: keep using this exact sequence instead of trying to optimize input handling.

Also note:

- library/game ordering in RPCSX can reshuffle by recency
- before opening `Fat Princess`, take a screenshot of the library view and confirm the tile position visually
- earlier mistakes happened because `A` was triggered while focus was on the wrong game

## Important Behavioral Findings

### 1. The RPCSX banner can lie about the loaded core

The top banner in the RPCSX UI can show a custom core name/version even when the process is still mapping a different `.so`.

Reliable validation method:

- inspect `/proc/<pid>/maps`
- confirm the actual mapped `librpcsx*.so`

Forcing the intended core involved:

- editing `/data/data/net.rpcsx/shared_prefs/app_prefs.xml`
- avoiding fallback to the stock library

The stock library that repeatedly needed to be avoided was:

- `v20251011-e27926d-armv8-a.so`

Suggested anti-stale step used during testing:

- rename or move the stock versioned `.so` so RPCSX cannot silently fall back to it

## Crash Reproduction Path

Repro path that consistently mattered:

1. Start RPCSX
2. Confirm the intended `.so` is actually loaded
3. Launch `Fat Princess`
4. Wait around one minute
5. Repeatedly send the exact controller `A` press sequence every few seconds
6. This eventually simulates selecting the `Accept` button on the online terms / agreement flow
7. Observe logs in parallel

Observed behavior:

- the game returns to the RPCSX library after the crash
- the crash is reproducible

## Core Crash Conclusion So Far

The most important stable crash signature:

- `Segfault reading location 0000000000000048 at 000000735c8e3158`

The faulting PC is inside:

- `/vendor/lib64/egl/libGLES_mali.so`

This is the central conclusion from the earlier debugging:

- the crash looks like a Mali driver crash triggered by a specific Vulkan shader/pipeline combination
- it does not currently look like a normal high-confidence RPCSX logic bug with an obvious local fix

## Key Pipeline / Shader Identifiers

The relevant pipeline identifiers already captured were:

- `vp_id=14`
- `fp_id=15`
- `pipe_hash=0xb576a592dabad65d`

These should be treated as the primary target for the next round of instrumentation.

## Local Code Changes Already Made In `/Users/longn/github/forks/rpcsx`

The following areas were instrumented or adjusted:

- build tag plumbing in:
  - `CMakeLists.txt`
  - `rpcs3/CMakeLists.txt`
  - `rpcs3/rpcs3_version.cpp`
- fatal-context TLS in:
  - `rpcs3/util/Thread.h`
  - `rpcs3/util/Thread.cpp`
- Vulkan pipeline instrumentation in:
  - `rpcs3/Emu/RSX/VK/VKPipelineCompiler.h`
  - `rpcs3/Emu/RSX/VK/VKPipelineCompiler.cpp`
  - `rpcs3/Emu/RSX/VK/VKProgramBuffer.h`
- shader module logging in:
  - `rpcs3/Emu/RSX/VK/VKVertexProgram.cpp`
  - `rpcs3/Emu/RSX/VK/VKFragmentProgram.cpp`
- minor Android/build fixes in:
  - `rx/CMakeLists.txt`
  - `3rdparty/zstd/CMakeLists.txt`

The repo was dirty with these changes already applied. Do not revert them casually.

## Specific Instrumentation Already Added

Examples of useful prior logging:

- `VKVertexProgram.cpp`
  - logs compiled Vulkan vertex shader id, handle, and source byte count
- `VKFragmentProgram.cpp`
  - logs compiled Vulkan fragment shader id, handle, and source byte count
- `VKProgramBuffer.h`
  - debug label includes `vp_id`, `fp_id`, `pipe_hash`, shader handles, and whether async compilation is involved
- `VKPipelineCompiler.cpp`
  - logs pipeline job / inline compile context
  - sets fatal context
  - contains a Mali-specific workaround attempt to force inline compilation rather than deferred compilation

## Result of the Mali Inline-Compilation Workaround

One attempted workaround forced inline pipeline compilation on ARM Mali instead of deferred worker compilation.

Result:

- this changed where the work happened
- but the crash still landed in `libGLES_mali.so`

Conclusion:

- removing deferred compilation was not sufficient
- the issue still looks driver-side, likely triggered by the same shader/pipeline pair

## Release Sweep Already Completed

There was a systematic sweep of older Android `librpcsx.so` builds from:

- `https://github.com/RPCSX/rpcsx-build/releases`

Method:

- test both:
  - `librpcsx-android-arm64-v8a-armv8-a.so`
  - `librpcsx-android-arm64-v8a-armv8.1-a.so`
- force RPCSX to use the intended library
- verify the mapped library in `/proc/<pid>/maps`
- launch `Fat Princess`
- use the exact `A`-button event sequence to reach the crash point

Summary of results:

- 26 valid tests
- 13 release tags
- from `v20251011-8cfb4e8` down through `v20250921-36b9e96`
- both `armv8-a` and `armv8.1-a`
- every completed run reproduced the same crash signature
- no meaningful behavior difference between `armv8-a` and `armv8.1-a`

Artifacts from that sweep:

- `/Users/longn/github/forks/rpcsx/_artifacts/release-sweep-20260620T123507Z/summary.tsv`
- corresponding files under `/Users/longn/github/forks/rpcsx/_artifacts/release-sweep-20260620T123507Z/`

One interrupted result should be ignored:

- `v20250921-2255d30 armv8-a`

## OpenGL Investigation Outcome

The user temporarily switched RPCSX to OpenGL and launched `Fat Princess`.

Observed result:

- the game loaded
- but the output was black screen instead of a functional render path
- no equivalent crash there, but also no working graphics

Code inspection showed:

- Android `init_gs_render` only handles `NullGSRender` and `VKGSRender`
- Android `GraphicsFrame` context methods are effectively stubs
- GL backend sources are excluded on Android in the build

Conclusion:

- OpenGL is effectively unimplemented on Android in the current RPCSX port
- it is not a practical workaround right now

## APS3E Side Check

A quick check of `https://github.com/aenu1/aps3e` found:

- some GLES-oriented code and Android-specific OpenGL headers
- but Android-side renderer init still only clearly instantiated `VKGSRender`
- GL sources were also excluded on Android there

Conclusion:

- APS3E shows partial GLES adaptation work
- but not a clearly usable Android OpenGL renderer path for this problem

## Last Stable Status Before Handoff

The previous agent’s status was effectively:

- reproduction is solid
- the crash consistently points into Mali’s graphics driver
- older RPCSX release cores do not avoid the crash
- OpenGL on Android is not currently a usable escape hatch
- the best remaining RPCSX-side next step is to dump the exact crashing shader/pipeline state and see whether a very narrow Mali-specific workaround is possible

## Immediate Next Suggestion

Proceed with targeted Vulkan instrumentation around the exact crashing pair:

- `vp_id=14`
- `fp_id=15`
- `pipe_hash=0xb576a592dabad65d`

The practical goal is to capture:

- full shader sources for the targeted vertex and fragment programs
- any relevant pipeline create-state that can be logged cheaply and safely
- enough context to try a narrow workaround for just this pipeline on Mali

Examples of plausible next experiments:

- dump shader source text for only the targeted IDs instead of for every shader
- dump the exact pipeline state attached to the targeted `pipe_hash`
- try a targeted state workaround for only that pipeline on Mali
- if shader source reveals a suspicious construct, try a narrower codegen or state adjustment only for that case

## Suggested Resume Checklist

1. Work in `/Users/longn/github/forks/rpcsx`
2. Inspect current instrumentation in:
   - `rpcs3/Emu/RSX/VK/VKPipelineCompiler.cpp`
   - `rpcs3/Emu/RSX/VK/VKVertexProgram.cpp`
   - `rpcs3/Emu/RSX/VK/VKFragmentProgram.cpp`
   - `rpcs3/Emu/RSX/VK/VKProgramBuffer.h`
3. Add targeted dumps for `vp_id=14`, `fp_id=15`, `pipe_hash=0xb576a592dabad65d`
4. Sync to `ctower`
5. Build inside Docker according to `_builder/docker-compose.yml`
6. Copy the built `.so` back to this Mac
7. Install the `.so` on the Android device
8. Force RPCSX to use it via `app_prefs.xml`
9. Verify the actual mapped library in `/proc/<pid>/maps`
10. Screenshot the library before selecting `Fat Princess`
11. Launch the correct game
12. Reproduce using the exact known-good `event5` `A`-button sequence
13. Collect logs and inspect whether the targeted shader/pipeline dump reveals a narrow workaround opportunity

## Caution Notes

- Do not trust the RPCSX UI banner alone for which core is loaded
- Do not assume the game tile ordering is stable
- Do not replace the user’s exact `A`-button input sequence with a different approach
- Do not treat OpenGL on Android as a viable fallback without implementing substantial missing backend support
- Do not expect older release cores to solve this automatically; that was already tested

## Bottom-Line Working Theory

Current best theory:

- `Fat Princess` triggers a specific Vulkan shader/pipeline configuration in RPCSX
- that configuration causes a crash inside the Orange Pi / Android Mali graphics driver
- a fix is most likely to require either:
  - a very narrow RPCSX-side workaround for that exact shader/pipeline on Mali, or
  - a different GPU driver / OS stack outside the app

The next agent should continue by extracting the exact shader and pipeline state for the already identified `vp_id`, `fp_id`, and `pipe_hash`.
