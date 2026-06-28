# source droid-config.sh before this one
_tmp_script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$_tmp_script_dir/droid-config.sh"

function __old_retrosync() {
	# rsync preset games to batocera
	dirPath='/Users/longn/Downloads/retrogaming'
	#echo $dirPath; return

    ipAddr=192.168.0.115
    target="root@$ipAddr:/userdata"

	# rsync bios files
	#rsync -avzru --exclude={'.DS_Store','_ignore'} $dirPath/bios/			$target/bios/

	# rsync games
	rsync -avzru --exclude={'.DS_Store','_ignore'} $dirPath/roms/fbneo/ 	$target/roms/fbneo/
	rsync -avzru --exclude={'.DS_Store','_ignore'} $dirPath/roms/mame/ 		$target/roms/mame/
	rsync -avzru --exclude={'.DS_Store','_ignore'} $dirPath/roms/neogeo/ 	$target/roms/neogeo/
	rsync -avzru --exclude={'.DS_Store','_ignore'} $dirPath/roms/nes/ 		$target/roms/nes/
	rsync -avzru --exclude={'.DS_Store','_ignore'} $dirPath/roms/psx/ 		$target/roms/psx/
	rsync -avzru --exclude={'.DS_Store','_ignore'} $dirPath/roms/snes/ 		$target/roms/snes/
	# more UI advance
	rsync -avzru --exclude={'.DS_Store','_ignore'} $dirPath/roms/n64/ 		$target/roms/n64/
}
function _old_batocera_retro-sync() {
    local dirPath="/Users/longn/Downloads/retrogaming"
    # local ipAddr="192.168.0.115"	# odroid xu4
    local ipAddr="BATOCERA.local"	# orange pi 5
    local target="root@$ipAddr:/userdata"

    local rsync_opts=(
        -avzu
        --exclude='.DS_Store'
        --exclude='_ignore'
    )

    # BIOS
    rsync "${rsync_opts[@]}" "$dirPath/bios/" "$target/bios/"

    # following systems are known to have jitter perf on xu4 board - not worth playing, no fun!
    # n64, 3ds, nds, psp, dreamcast
    # not supported on xu4: 3ds, nds

    # ROM systems
    #local systems=(
    #    fbneo
    #    mame
    #    neogeo
    #    nes
    #    psx
    #    snes
    #    3do
    #    n64
    #    nds
    #    psp
    #    dreamcast
    #    gamecube
    #)

    # ROM systems
    local systems=(
        saturn
    )

    for sys in "${systems[@]}"; do
        rsync "${rsync_opts[@]}" "$dirPath/roms/$sys/" "$target/roms/$sys/"
    done

    # custom scripts as service
    rsync "${rsync_opts[@]}" "$dirPath/scripts/" "$target/scripts/"
    rsync "${rsync_opts[@]}" "$dirPath/system/services/" "$target/system/services/"
    #scp "$dirPath/system/.profile" "$target/system/.profile"

    # custom configs
    rsync "${rsync_opts[@]}" "$dirPath/system/saturn/" "$target/system/saturn/"
    rsync "${rsync_opts[@]}" "$dirPath/system/configs/" "$target/system/configs/"
}
function _old_batocera_retro-backup() {
	# odroid xu4 board
    #local board_target="root@192.168.0.115:/userdata/"
    #local board_dir="/Users/longn/Downloads/retrogaming/_ignore/backup_xu4/userdata/"

    # orange pi 5 board
    local board_target="root@BATOCERA.local:/userdata/"
    local board_dir="/Users/longn/Downloads/retrogaming/_ignore/backup_orpi5/userdata/"

    mkdir -p $board_dir

    rsync -avzru --progress --exclude={'.DS_Store','_ignore','roms/'} --delete $board_target $board_dir
}

function _old_retro-sync() {
    local dirPath="/Users/longn/Downloads/retrogaming"
    local ipAddr="192.168.0.99"	# orange pi 5, orange pi OS
    local target="u0_a77@$ipAddr:/sdcard/RetroGames"
    local tmp_target="u0_a77@$ipAddr:/sdcard/Download/retrodroid"

    local rsync_opts=(
        -avzu
        --exclude='.DS_Store'
        --exclude='_ignore'
        -e "ssh -p $SSH_PORT"
    )

    # BIOS
    #rsync "${rsync_opts[@]}" "$dirPath/bios/" "$target/bios/"

    # emulator files for individual emulators setup
    rsync "${rsync_opts[@]}" "$dirPath/_emulator-files/ps2" "$tmp_target/_emulator-files/"
    rsync "${rsync_opts[@]}" "$dirPath/_emulator-files/ps3" "$tmp_target/_emulator-files/"
    rsync "${rsync_opts[@]}" "$dirPath/_emulator-files/psvita" "$tmp_target/_emulator-files/"

    # ROM systems
    local systems=(
    	3do
		dreamcast
		fbneo
		gamegear
		gc
		genesis
		mame
		n3ds
		n64
		nds
		neogeo
		neogeocd
		nes
		ps2
		ps3
		psp
		psvita
		psx
		saturn
		snes
		switch
		xbox
    )

    for sys in "${systems[@]}"; do
        rsync "${rsync_opts[@]}" "$dirPath/roms/$sys/" "$target/ROMs/$sys/"
    done
}

function retro-ssh() {
	ssh -p $SSH_PORT $SSH_USER@$DROID_ADDRESS
}

function retro-sync() {
    local dirPath=$LOCAL_RETROGAMING_DIR
    local ipAddr=$DROID_ADDRESS    # orange pi 5, orange pi OS
    local target="$SSH_USER@$ipAddr:/sdcard/RetroGames"
    local tmp_target="$SSH_USER@$ipAddr:/sdcard/Download/retrodroid"

    local rsync_opts=(
        -avzu
        --exclude='.DS_Store'
        --exclude='_ignore'
        -e "ssh -p $SSH_PORT"
    )

    # BIOS
    # rsync "${rsync_opts[@]}" "$dirPath/bios/" "$target/bios/"

    # emulator files for individual emulators setup
    rsync "${rsync_opts[@]}" "$dirPath/_emulator-files/" "$tmp_target/_emulator-files/"

    # ROM systems: sync every subfolder under roms/ except a small exclusion list
    local excluded_systems=(
        _ignore
    )

    local rom_dir
    local sys
    while IFS= read -r rom_dir; do
        sys="$(basename "$rom_dir")"

        if [[ ! -d "$rom_dir" ]]; then
            continue
        fi

        if [[ " ${excluded_systems[*]} " == *" $sys "* ]]; then
            continue
        fi

        rsync "${rsync_opts[@]}" "$rom_dir/" "$target/ROMs/$sys/"
    done < <(
        find "$dirPath/roms" -mindepth 1 -maxdepth 1 -type d | sort
    )
}

function retro-view() {
  scrcpy --no-audio
}

