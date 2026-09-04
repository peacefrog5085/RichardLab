#!/usr/bin/env bash

LAB="$HOME/RichardLab"

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  MEDIA LAB                                         ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║  OBS / Kdenlive / FFmpeg / YouTube                 ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo
    echo "  [1] Recording"
    echo "  [2] Editing"
    echo "  [3] Rendering"
    echo "  [4] Projects"
    echo "  [5] Publishing"
    echo "  [0] RETURN TO MISSION CONTROL"
    echo
    read -rp "MEDIA LAB > " choice
    case "$choice" in
        1)
            echo
            echo "Selected: Recording"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        2)
            echo
            echo "Selected: Editing"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        3)
            echo
            echo "Selected: Rendering"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        4)
            echo
            echo "Selected: Projects"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        5)
            echo
            echo "Selected: Publishing"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        0)
            exit 0
            ;;
        *)
            echo
            echo "Unknown command."
            sleep 1
            ;;
    esac
done
