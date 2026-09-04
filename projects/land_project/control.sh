#!/usr/bin/env bash

LAB="$HOME/RichardLab"

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  FIND RICHARD SOME DAMN LAND                       ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║  Property / Land Acquisition                       ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo
    echo "  [1] Property Candidates"
    echo "  [2] Tax Sales"
    echo "  [3] Ownership / Legal"
    echo "  [4] Costs"
    echo "  [5] Research Notes"
    echo "  [0] RETURN TO MISSION CONTROL"
    echo
    read -rp "LAND PROJECT > " choice
    case "$choice" in
        1)
            echo
            echo "Selected: Property Candidates"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        2)
            echo
            echo "Selected: Tax Sales"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        3)
            echo
            echo "Selected: Ownership / Legal"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        4)
            echo
            echo "Selected: Costs"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        5)
            echo
            echo "Selected: Research Notes"
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
