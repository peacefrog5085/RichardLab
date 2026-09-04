#!/usr/bin/env bash

LAB="$HOME/RichardLab"

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  THE VALUE FLOW PROJECT                            ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║  Marvel → Disney / Value Flow Map                  ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo
    echo "  [1] Case Studies"
    echo "  [2] Value Flow Map"
    echo "  [3] Evidence"
    echo "  [4] Calculations"
    echo "  [5] Project Notes"
    echo "  [0] RETURN TO MISSION CONTROL"
    echo
    read -rp "VALUE FLOW > " choice
    case "$choice" in
        1)
            echo
            echo "Selected: Case Studies"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        2)
            echo
            echo "Selected: Value Flow Map"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        3)
            echo
            echo "Selected: Evidence"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        4)
            echo
            echo "Selected: Calculations"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        5)
            "$LAB/projects/value_flow/notes.sh"
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
