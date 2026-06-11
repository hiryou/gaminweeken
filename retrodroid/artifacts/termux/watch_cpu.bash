watch_cpu() {
    if command -v watch >/dev/null 2>&1; then
        watch -n 2 'for z in /sys/class/thermal/thermal_zone*; do [ -f "$z/temp" ] || continue; printf "%s " "$(basename "$z")"; awk "{printf \"%.1fC\\n\", \$1/1000}" "$z/temp"; done'
        return
    fi

    while :; do
        clear
        for z in /sys/class/thermal/thermal_zone*; do
            [ -f "$z/temp" ] || continue
            printf "%s " "$(basename "$z")"
            awk '{printf "%.1fC\n", $1/1000}' "$z/temp"
        done
        sleep 2
    done
}
