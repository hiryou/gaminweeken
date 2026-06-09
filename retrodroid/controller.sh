#!/data/data/com.termux/files/usr/bin/sh

# Ensure terminal drops into the script's directory
cd "$(dirname "$0")"

while true; do
    clear
    echo "========================================================="
    echo "    ORANGE PI 5 APPLIANCE: CENTRAL CONTROLLER INTERFACE  "
    echo "========================================================="
    echo " [1] Initialize System (Create Folders & Enable SSH Boot)"
    echo " [2] Bootstrap Emulators (Download All Latest APK Files)"
    echo " [3] Manage Game Artwork (Scrape & Sync ES-DE Covers)"
    echo " [4] Exit Link Terminal"
    echo "========================================================="
    read -p "Enter your selection (1-4): " choice

    case $choice in
        1)
            echo -e "\n[*] Launching System Initializer..."
            python ./scripts/initialize_system.py
            read -p "Press Enter to return to menu..." temp
            ;;
        2)
            echo -e "\n[*] Launching Emulator Bootstrapper..."
            python ./scripts/bootstrap_apks.py
            read -p "Press Enter to return to menu..." temp
            ;;
        3)
            echo -e "\n[*] Launching Unified Artwork Manager..."
            python ./scripts/manage_art.py
            ;;
        4)
            echo -e "\n[*] Closing Control Interface. Goodbye!"
            break
            ;;
        *)
            echo -e "\n[-] Invalid menu choice. Please select 1-4."
            sleep 2
            ;;
    esac
done


