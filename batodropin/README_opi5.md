# What is this project

Set of files to drop-in after installation of a base Batocera to support custom emulators 

## Worklog on Orange pi 5 board

About playing nintendo 3ds on orange pi 5 board, it seemed possible with some custom setup, as mentioned on this
[reddit thread](https://www.reddit.com/r/SBCGaming/comments/13871g9/choosing_the_right_sbc_for_3ds_emulation/) 
and possibly this being the right github [Vulkan fork](https://github.com/Ishan09811/Citra-Enhanced) ?

Better 3DS emulator: [Azahar](https://github.com/azahar-emu/azahar)

Conceptually the steps are
* manually place emulator binary somewhere under /userdata
* add custom EmulationStation system entry
* point that system to a launcher script
* put 3DS ROMs in /userdata/roms/3ds

But it only works if you have an ARM64 Linux Azahar/Citra binary that runs on Batocera’s libraries.

### Overview

Minimal structure

* /userdata/system/azahar/azahar
* /userdata/system/azahar/lib/*.so lib files custom compiled on Linux aarch64
* /userdata/system/scripts/launch-azahar.sh
* /userdata/roms/3ds/

For `launch-azahar.sh`
```shell
mkdir -p /userdata/system/scripts

cat > /userdata/system/scripts/launch-azahar.sh <<'EOF'
#!/bin/bash
ROM="$1"

export LD_LIBRARY_PATH="/userdata/system/azahar/lib:$LD_LIBRARY_PATH"
export XDG_RUNTIME_DIR="/tmp/runtime-root"
mkdir -p "$XDG_RUNTIME_DIR"

exec /userdata/system/azahar/azahar "$ROM"
EOF

chmod +x /userdata/system/scripts/launch-azahar.sh
```

For 3ds game entry
```shell
cp /usr/share/emulationstation/es_systems.cfg \
   /userdata/system/configs/emulationstation/es_systems.cfg
   
<system>
    <fullname>Nintendo 3DS</fullname>
    <name>3ds</name>
    <manufacturer>Nintendo</manufacturer>
    <release>2011</release>
    <hardware>portable</hardware>
    <path>/userdata/roms/3ds</path>
    <extension>.3ds .3DS .cci .CCI .cxi .CXI</extension>
    <command>/userdata/system/scripts/launch-azahar.sh %ROM%</command>
    <platform>3ds</platform>
    <theme>3ds</theme>
</system>

# or another one
<system>
        <fullname>Nintendo 3DS</fullname>
        <name>3ds</name>
        <manufacturer>Nintendo</manufacturer>
        <release>2011</release>
        <hardware>portable</hardware>
        <path>/userdata/roms/3ds</path>
        <extension>.3ds .3DS .cci .CCI .cxi .CXI .cia .CIA</extension>
        <command>/userdata/system/scripts/launch-azahar.sh %ROM%</command>
        <platform>3ds</platform>
        <theme>3ds</theme>
        <emulators>
            <emulator name="azahar">
                <cores>
                    <core default="true">azahar</core>
                </cores>
            </emulator>
        </emulators>
  </system>

# then
batocera-es-swissknife --restart
```

### Azahar custom build worklogs

Cleanest attempt: cross-build inside an ARM64 Ubuntu container using QEMU

On host machine: prep a ARM64 Ubuntu container
```shell
# 0) host prep
sudo apt update
sudo apt install -y docker.io qemu-user-static binfmt-support git
sudo systemctl enable --now docker

# optional if your user is not in docker group
sudo usermod -aG docker "$USER"
# log out/in after this if needed

# 1) enable multi-arch emulation
docker run --privileged --rm tonistiigi/binfmt --install arm64

# 2) workspace
mkdir -p ~/Downloads/retrogaming/custom/azahar-build
cd ~/Downloads/retrogaming/custom/azahar-build

# 3) run ARM64 Ubuntu container
docker run --rm -it --platform linux/arm64 \
  -v "$PWD":/work \
  ubuntu:24.04 bash
```

Inside the container - DONE: without ref to [batocera.linux](https://github.com/batocera-linux/batocera.linux)
```shell
apt update

export DEBIAN_FRONTEND=noninteractive

cat > /usr/sbin/policy-rc.d <<'EOF'
#!/bin/sh
exit 101
EOF
chmod +x /usr/sbin/policy-rc.d

apt install -y --no-install-recommends \
  git ca-certificates build-essential cmake ninja-build pkg-config \
  python3 python3-pip \
  qt6-base-dev qt6-base-dev-tools qt6-tools-dev qt6-tools-dev-tools \
  libssl-dev libfmt-dev libboost-dev liblz4-dev zlib1g-dev \
  libsdl2-dev libvulkan-dev glslang-tools spirv-tools \
  libavcodec-dev libavformat-dev libavutil-dev libswscale-dev \
  libx11-dev libxext-dev libxi-dev libxrandr-dev libxrender-dev \
  libxcb1-dev libxcb-xinerama0-dev libwayland-dev
  
# Missing while build on linux/arm64 ubuntu:24.04
apt-cache search qt6 | grep -i multimedia
apt install -y --no-install-recommends qt6-multimedia-dev qt6-base-private-dev

git clone --recursive https://github.com/azahar-emu/azahar.git -> /work/azahar
cd /work/azahar
rm -rf build

# prep build configs
cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DENABLE_QT=ON \
  -DENABLE_SDL2=ON
  
# then build
cmake --build build -j"$(nproc)"
# this build will take a long time

# If it throws another missing Qt component, install the matching package. Common ones:
apt install -y --no-install-recommends \
  qt6-base-dev \
  qt6-tools-dev \
  qt6-tools-dev-tools \
  qtmultimedia6-dev \
  qt6-wayland-dev
  
# If qt6-multimedia-dev is also missing, enable Ubuntu universe:
apt install -y --no-install-recommends software-properties-common
add-apt-repository universe
apt update
apt install -y --no-install-recommends qt6-multimedia-dev
```

If you get error `Errors were encountered while processing: systemd E: Sub-process /usr/bin/dpkg returned an error code (1)`
fix like  this:
```shell
dpkg -l | grep systemd

# If actual systemd package is installed and broken, remove it:
apt purge -y systemd systemd-sysv systemd-timesyncd libpam-systemd libnss-systemd || true
apt-get -f install -y
dpkg --configure -a
# Do not remove libsystemd0; many packages may depend on that harmless library.
```

Inside the container - recommended way: ref to [batocera.linux](https://github.com/batocera-linux/batocera.linux). This
is to build against Batocera’s own Buildroot output/toolchain for the exact Batocera branch/version.
```shell
# 1) Clone Batocera
git clone https://github.com/batocera-linux/batocera.linux.git
cd batocera.linux

# 2) Checkout the matching Batocera version/branch/tag
git tag | grep -i 42
git checkout <v42-tag-or-commit>

# Then build or at least prepare the Orange Pi 5 target
make list-defconfigs | grep -i orange
make list-defconfigs | grep -i rk3588
make orangepi5-build

# After Batocera builds, you get a matching sysroot/toolchain under something like:
# output/orangepi5/host/
# output/orangepi5/staging/
# output/orangepi5/target/

# Then build Azahar using that cross compiler/sysroot, conceptually:
export BATOCERA_OUT=$PWD/output/orangepi5
export PATH="$BATOCERA_OUT/host/bin:$PATH"

git clone --recursive https://github.com/azahar-emu/azahar.git
cd azahar

cmake -S . -B build -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_SYSROOT="$BATOCERA_OUT/staging" \
  -DCMAKE_FIND_ROOT_PATH="$BATOCERA_OUT/staging" \
  -DCMAKE_INSTALL_PREFIX=/userdata/system/azahar

cmake --build build -j$(nproc)
# this build will take a long time
```

After build, preserve azahar binary & its ARM64 required libs. Still inside build container:
```shell
mkdir -p /work/out/azahar/lib

cp build/bin/Release/azahar /work/out/azahar/

ldd /work/out/azahar/azahar | awk '/=> \// {print $3}' | sort -u \
  | while read -r lib; do
      cp "$lib" /work/out/azahar/lib/
    done
cp /lib/ld-linux-aarch64.so.1 /work/out/azahar/lib/
# there should be 99 lib files in total
```

Why this matters: If you build in ubuntu:24.04, you may get err like "GLIBC_2.39 not found" on Batocera. If you build 
against Batocera’s Buildroot sysroot, your binary links against the same libc/runtime family Batocera uses.

### Extra: check GLIBC version support

To check what glibc versions your Azahar binary requires:
```shell
strings /userdata/system/azahar/azahar | grep 'GLIBC_' | sort -V | tail
```

Inspect the Orange Pi 5 image directly
```shell
# On your Linux server:
mkdir -p ~/tmp/bato-opi5
cd ~/tmp/bato-opi5

gunzip -c ~/Downloads/retrogaming/batocera-rk3588-orangepi-5-42-20251015.img.gz > opi5.img

sudo losetup --find --show -P opi5.img
# Assume it prints:
# /dev/loop7

# then, Mount boot partition:
sudo mkdir -p /mnt/bato-boot
sudo mount /dev/loop7p1 /mnt/bato-boot

find /mnt/bato-boot -maxdepth 3 -type f | grep -E 'batocera|squashfs'
sudo apt install -y squashfs-tools
mkdir -p rootfs
unsquashfs -d rootfs /mnt/bato-boot/boot/batocera

# Now check glibc symbols:
find rootfs -name 'libc.so.6' -o -name 'ld-linux-aarch64.so.1'
# then
strings rootfs/lib/libc.so.6 | grep '^GLIBC_' | sort -V | tail
# or if located elsewhere:
strings rootfs/usr/lib/libc.so.6 | grep '^GLIBC_' | sort -V | tail
```

OK IF: Azahar max required <= Batocera max provided

Result found OK for Orange pi 5 board batocera v42
```text
Your Azahar binary requires max: GLIBC_2.38
Your Orange Pi 5 Batocera v42 image provides: GLIBC_2.39
So:
Azahar requirement: <= GLIBC_2.38
Batocera provides:     GLIBC_2.39
Result: OK
```

So glibc is not the blocker for this build. Next likely blockers are:
```text
missing Qt/SDL/Vulkan/etc .so files
Qt platform plugins
GPU/display runtime issues
```

Check of Vulkan/OpenGL mismatch: moderate, not huge. From extracted rootfs:
```shell
# Mesa / OpenGL / Vulkan libs
find rootfs -iname '*vulkan*' -o -iname '*mesa*' -o -iname '*EGL*' -o -iname '*GLES*' -o -iname '*GLX*'

# Vulkan ICD files
find rootfs -path '*vulkan/icd.d*' -type f -print -exec cat {} \;

# Mesa version clues
find rootfs -type f \( -name 'libvulkan*.so*' -o -name 'libEGL*.so*' -o -name 'libGLES*.so*' \) -print

# GPU device/userland clues
find rootfs -iname '*panfrost*' -o -iname '*panfork*' -o -iname '*mali*'

# Also inspect kernel modules if present:
find rootfs -type f -name '*.ko*' | grep -Ei 'panfrost|mali|gpu|drm'
```

### Azahar check after build

Correct hierarchy checks
```text
Level 1: CPU architecture match
Ubuntu ARM64 Docker gives this.

Level 2: Linux runtime/library match
Bundled .so files may solve this.

Level 3: board GPU/display/input compatibility
Only real testing on Orange Pi 5 Batocera proves this.

Level 4: perfect Batocera-native integration
Requires building as a Batocera package with Batocera Buildroot.
```

Re-check on Batocera
```shell
LD_LIBRARY_PATH=/userdata/system/azahar/lib ldd /userdata/system/azahar/azahar | grep "not found"

# launch help without triggering Qt display
QT_QPA_PLATFORM=offscreen /work/out/azahar/azahar --help
```

On a live board later, check of Vulkan/OpenGL mismatch:
```shell
ls -l /dev/dri
vulkaninfo --summary
glxinfo -B
eglinfo

# If vulkaninfo is absent:
find /usr /userdata -name vulkaninfo 2>/dev/null
```


















