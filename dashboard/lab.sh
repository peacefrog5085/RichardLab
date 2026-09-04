#!/usr/bin/env bash

LAB="$HOME/RichardLab"

show_header() {
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║              RICHARD DIGITAL LAB                    ║"
    echo "║                  MISSION CONTROL v2                 ║"
    echo "╠══════════════════════════════════════════════════════╣"
}

pause_screen() {
    echo
    read -rp "Press ENTER to return to Mission Control..."
}

while true; do
    show_header

    echo "║                                                      ║"
    echo "║  1) SYSTEM STATUS                                    ║"
    echo "║  2) PROCESS WATCH                                    ║"
    echo "║  3) SYSTEM SCAN                                     ║"
    echo "║  4) EXPERIMENTS                                     ║"
    echo "║  5) REPORTS                                         ║"
    echo "║  6) MODULE STATUS                                   ║"
    echo "║  7) GIT STATUS                                      ║"
    echo "║                                                      ║"
    echo "║  Q) EXIT                                             ║"
    echo "║                                                      ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo

    read -rp "RICHARD@LAB > " choice

    case "$choice" in

        1)
            python "$LAB/mission_control/lab_status.py"
            pause_screen
            ;;

        2)
            clear
            python "$LAB/mission_control/process_probe.py"
            ;;

        3)
            clear
            "$LAB/dashboard/system-scan.sh"
            pause_screen
            ;;

        4)
            clear
            echo "╔══════════════════════════════════════════════════════╗"
            echo "║                    EXPERIMENTS                      ║"
            echo "╚══════════════════════════════════════════════════════╝"
            echo
            find "$LAB/experiments" -maxdepth 1 -type f -printf "%f\n" | sort
            pause_screen
            ;;

        5)
            clear
            echo "╔══════════════════════════════════════════════════════╗"
            echo "║                      REPORTS                        ║"
            echo "╚══════════════════════════════════════════════════════╝"
            echo
            find "$LAB/reports" -maxdepth 1 -type f -printf "%TY-%Tm-%Td %TH:%TM  %f\n" \
                | sort -r
            pause_screen
            ;;

        6)
            clear
            python "$LAB/mission_control/lab_status.py"
            echo
            echo "MODULE DIRECTORIES"
            echo "────────────────────────────────────────"
            for module in ai data dashboard experiments forensics knowledge media mission_control reports value_flow; do
                if [ -d "$LAB/$module" ]; then
                    count=$(find "$LAB/$module" -type f | wc -l)
                    printf "%-18s %5s files\n" "$module" "$count"
                else
                    printf "%-18s MISSING\n" "$module"
                fi
            done
            pause_screen
            ;;

        7)
            clear
            echo "╔══════════════════════════════════════════════════════╗"
            echo "║                    GIT STATUS                       ║"
            echo "╚══════════════════════════════════════════════════════╝"
            echo
            git -C "$LAB" status
            echo
            echo "RECENT COMMITS"
            echo "────────────────────────────────────────"
            git -C "$LAB" log --oneline -5
            pause_screen
            ;;

        q|Q)
            clear
            echo "RICHARD DIGITAL LAB: OFFLINE"
            exit 0
            ;;

        *)
            echo
            echo "Invalid command."
            sleep 1
            ;;

    esac
done
