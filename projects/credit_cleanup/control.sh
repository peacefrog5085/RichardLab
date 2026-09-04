#!/usr/bin/env bash

LAB="$HOME/RichardLab"

while true; do
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  CREDIT FORENSIC CLEANUP                           ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║  Analyze → Document → Dispute → Recover            ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo
    echo "  [1] Accounts"
    echo "  [2] Inquiries"
    echo "  [3] Evidence"
    echo "  [4] Disputes"
    echo "  [5] Recovery Plan"
    echo "  [0] RETURN TO MISSION CONTROL"
    echo
    read -rp "CREDIT LAB > " choice
    case "$choice" in
        1)
            echo
            echo "Selected: Accounts"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        2)
            echo
            echo "Selected: Inquiries"
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
            echo "Selected: Disputes"
            echo
            echo "This module is ready for the next build."
            read -rp "Press ENTER to continue..."
            ;;
        5)
            echo
            echo "Selected: Recovery Plan"
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
