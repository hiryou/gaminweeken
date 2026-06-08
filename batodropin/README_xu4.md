# YabaSanshiro (Sega Saturn) drop-in for Odroid XU4 / Batocera v43

Companion to the top-level README. Same conceptual flow as the Azahar/Orange Pi 5
notes, retargeted to:

* Board: **Odroid XU4** (Samsung Exynos 5422 — Cortex-A15 + A7, **32-bit ARMv7**)
* GPU:   **Mali-T628 MP6** (OpenGL ES 3.1, no usable Vulkan)
* OS:    **Batocera v43** for `odroidxu4` (glibc, 32-bit userland)
* Goal:  add a **standalone YabaSanshiro** binary as a drop-in emulator, because
  the stock v43 image for XU4 does not expose a `saturn` system (no
  `/userdata/roms/saturn` is created on first boot).

Why YabaSanshiro and not Kronos / Beetle-Saturn / Yabause:

* YabaSanshiro is the only Saturn emulator with a **GLES2/3 backend** designed
  for Mali-class mobile GPUs. Kronos requires desktop GL.
* It has a working build path on 32-bit ARM (this is what Retropie / ORA /
  earlier Batocera shipped on XU4).
* Source: <https://github.com/devmiyax/yabause>

## Hierarchy checks (XU4 reality)

```text
Level 1 — CPU architecture match
  Debian/Ubuntu linux/arm/v7 container provides this.

Level 2 — Linux runtime/library match
  Bundling YabaSanshiro's .so deps next to the binary handles this when the
  build's glibc is older-or-equal to Batocera v43's glibc. If not, rebuild
  against Batocera Buildroot (see "recommended path" below).

Level 3 — GPU / display / input compatibility
  Mali-T628 + GLES3 path. -DFORCE_GLES is mandatory; the desktop GL path
  will not link against Mali userspace drivers on XU4.

Level 4 — Batocera-native integration
  Package via Batocera Buildroot for the odroidxu4 defconfig.
```

## Target layout on the device

```text
/userdata/system/saturn/yabasanshiro/yabasanshiro       # the binary
/userdata/system/saturn/yabasanshiro/lib/*.so           # bundled libs (only if needed)
/userdata/system/saturn/yabasanshiro/shaders/           # bundled GLES shaders from the repo
/userdata/bios/saturn_bios.bin                   # optional but recommended
/userdata/system/scripts/launch-yabasanshiro.sh
/userdata/roms/saturn/                           # ROMs (.chd preferred, .cue/.bin, .iso)
```

### Launcher script

```shell
#!/bin/sh
mkdir -p /userdata/system/scripts

cat > /userdata/system/scripts/launch-yabasanshiro.sh <<'EOF'
#!/bin/bash
ROM="$1"
export LD_LIBRARY_PATH="/userdata/system/saturn/yabasanshiro/lib:$LD_LIBRARY_PATH"
# Mali-T628 needs GLES; force the right Qt/SDL platform on Batocera.
export SDL_VIDEODRIVER=x11
exec /userdata/system/saturn/yabasanshiro/yabasanshiro \
  --bios=/userdata/bios/saturn_bios.bin \
  --iso="$ROM"
EOF

chmod +x /userdata/system/scripts/launch-yabasanshiro.sh
```

EmulationStation system entry

```shell
# If you do not already have a local copy
mkdir -p /userdata/system/configs/emulationstation
cp /usr/share/emulationstation/es_systems.cfg \
   /userdata/system/configs/emulationstation/es_systems.cfg

# Append (or replace any existing saturn block) — keep the canonical
# Batocera system name "saturn" so theme + scraper just work:

<system>
    <fullname>Sega Saturn</fullname>
    <name>saturn</name>
    <manufacturer>Sega</manufacturer>
    <release>1994</release>
    <hardware>console</hardware>
    <path>/userdata/roms/saturn</path>
    <extension>.cue .CUE .chd .CHD .iso .ISO .ccd .CCD .m3u .M3U</extension>
    <command>/userdata/system/scripts/launch-yabasanshiro.sh %ROM%</command>
    <platform>saturn</platform>
    <theme>saturn</theme>
</system>

# then
mkdir -p /userdata/roms/saturn
batocera-es-swissknife --restart
```

Host prep

```shell
sudo apt update
sudo apt install -y docker.io qemu-user-static binfmt-support git
sudo systemctl enable --now docker
sudo usermod -aG docker "$USER"   # re-login after this

# Enable BOTH arm (armv7) and arm64 emulation
docker run --privileged --rm tonistiigi/binfmt --install arm,arm64

mkdir -p ~/Downloads/retrogaming/custom/saturn-build
cd ~/Downloads/retrogaming/custom/saturn-build

docker run --name yabasanshiro_xu4 --rm -it --platform linux/arm/v7 \
  -v "$PWD":/work \
  debian:bookworm bash
```

### Inside the container

```shell
apt update
export DEBIAN_FRONTEND=noninteractive

# Block service-start side-effects during install in chroot
cat > /usr/sbin/policy-rc.d <<'EOF'
#!/bin/sh
exit 101
EOF
chmod +x /usr/sbin/policy-rc.d

apt install -y --no-install-recommends \
  git ca-certificates build-essential cmake ninja-build pkg-config \
  python3 \
  libsdl2-dev libgl1-mesa-dev libgles2-mesa-dev libegl1-mesa-dev \
  libglu1-mesa-dev libglew-dev \
  zlib1g-dev libpng-dev libboost-dev \
  libopenal-dev \
  libavcodec-dev libavformat-dev libavutil-dev libswscale-dev \
  libx11-dev libxext-dev libxi-dev libxrandr-dev libxrender-dev

# YabaSanshiro source
git clone --recursive https://github.com/devmiyax/yabause.git /work/yabause
cd /work/yabause

# The standalone SDL frontend lives under yabause/
# CMake source root for the SDL build is yabause/yabause
cd yabause

rm -rf build
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DYAB_PORTS=sdl \
  -DYAB_WANT_SDL=ON \
  -DYAB_WANT_OPENAL=ON \
  -DYAB_WANT_C68K=ON \
  -DYAB_NETWORK=OFF \
  -DCMAKE_INSTALL_PREFIX=/work/out/yabasanshiro
  
# if hit with some issue due to 'build/' being wiped -> so libchdr needs to rebuild first: `build/`
cmake --build build -j"$(nproc)" --target libchdr

cmake --build build -j"$(nproc)"
cmake --install build

# Notes on the flags above: -DFORCE_GLES=ON / -DFORCE_GLES31=ON — required for Mali-T628; without it the build 
# tries desktop GL and the resulting binary won't link on XU4. Documented in the libretro YabaSanshiro CMake 
# conventions. -DYAB_PORTS=qt builds the Qt frontend; for a headless / SDL-only build try -DYAB_PORTS=sdl 
# (some forks use linux instead). Match what the current CMakeLists.txt in yabause/yabause/ actually offers — 
# the option names have drifted between commits. If qt is selected, also install qt6-base-dev qt6-multimedia-dev 
# (Qt6) or qtbase5-dev qtmultimedia5-dev (Qt5) depending on what the tree wants.

# On the build host (out of container), or inside if you mounted /work
ls /work/out/yabasanshiro
# bin/yabasanshiro  share/yabasanshiro/...

#mkdir -p staging/yabasanshiro/lib
#cp /work/out/yabasanshiro/bin/yabasanshiro staging/yabasanshiro/
#cp -r /work/out/yabasanshiro/share/yabasanshiro staging/yabasanshiro/share

# Collect .so deps that are NOT part of Batocera's base. Start empty and only
# add what `ldd ... | grep "not found"` complains about on the actual XU4.
mkdir -p /work/out/yabasanshiro/lib

ldd /work/out/yabasanshiro/bin/yabasanshiro | awk '/=> \// {print $3}' | sort -u \
  | while read -r lib; do cp "$lib" /work/out/yabasanshiro/lib/; done
cp /lib/ld-linux-armhf.so.3 /work/out/yabasanshiro/lib/

ls /work/out/yabasanshiro/lib/ | wc -l
```

### Build worklog — recommended path (Batocera Buildroot)
Same reasoning as the Azahar notes: building against Batocera's own toolchain guarantees the glibc/SDL2/Mesa ABI matches v43 on XU4 — no GLIBC_2.x surprises.

```shell
git clone https://github.com/batocera-linux/batocera.linux.git
cd batocera.linux

# v43-matching tag/branch
git tag | grep -i 43
git checkout <v43-tag-or-commit>

# Pick the XU4 defconfig
make list-defconfigs | grep -i xu4
make odroidxu4-build      # exact target name may differ; verify from list

# After Batocera builds, sysroot/toolchain live under:
#   output/odroidxu4/host/
#   output/odroidxu4/staging/
#   output/odroidxu4/target/

export BATOCERA_OUT=$PWD/output/odroidxu4
export PATH="$BATOCERA_OUT/host/bin:$PATH"

git clone --recursive https://github.com/devmiyax/yabause.git
cd yabause/yabause

cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_SYSROOT="$BATOCERA_OUT/staging" \
  -DCMAKE_FIND_ROOT_PATH="$BATOCERA_OUT/staging" \
  -DCMAKE_INSTALL_PREFIX=/userdata/system/saturn/yabasanshiro \
  -DFORCE_GLES=ON \
  -DFORCE_GLES31=ON \
  -DYAB_PORTS=sdl

cmake --build build -j"$(nproc)"
```

Post-deploy checks on the XU4

```shell
# Unresolved libs?
LD_LIBRARY_PATH=/userdata/system/saturn/yabasanshiro/lib ldd /userdata/system/saturn/yabasanshiro/yabasanshiro | grep "not found"

# Sanity-run without firing up ES (Mali driver must be present)
LD_LIBRARY_PATH=/userdata/system/saturn/yabasanshiro/lib \
  /userdata/system/saturn/yabasanshiro/yabasanshiro --help

# If GL/GLES init fails: confirm Mali userspace is loaded
ls /usr/lib/arm-linux-gnueabihf/ | grep -i mali
glxinfo -B 2>/dev/null | head    # if mesa-utils is around
```


