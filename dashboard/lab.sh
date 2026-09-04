#!/usr/bin/env bash

LAB="$HOME/RichardLab"

pause_screen() {
    echo
    read -rp "Press ENTER to return..."
}

show_header() {
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║              RICHARD DIGITAL LAB                    ║"
    echo "║                  MISSION CONTROL v2                 ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo
}

forensics_menu() {
    while true; do
        clear
        echo "╔══════════════════════════════════════════════════════╗"
        echo "║                 DIGITAL FORENSICS                   ║"
        echo "╠══════════════════════════════════════════════════════╣"
        echo "║                                                      ║"
        echo "║  1) SCAN DIRECTORY                                   ║"
        echo "║  2) COMPARE SNAPSHOTS                                ║"
        echo "║  3) BUILD TIMELINE                                   ║"
        echo "║  4) LIST REPORTS                                     ║"
        echo "║                                                      ║"
        echo "║  B) BACK                                             ║"
        echo "║                                                      ║"
        echo "╚══════════════════════════════════════════════════════╝"
        echo

        read -rp "FORENSICS@LAB > " choice

        case "$choice" in

            1)
                echo
                read -rp "Directory to scan [$LAB]: " target
                target="${target:-$LAB}"

                python "$LAB/forensics/file_forensics.py" "$target"
                pause_screen
                ;;

            2)
                echo
                echo "Available forensic snapshots:"
                echo
                python "$LAB/forensics/report_utils.py"
                echo
                read -rp "OLD report path: " old_report
                read -rp "NEW report path: " new_report

                python "$LAB/forensics/compare.py" \
                    "$old_report" \
                    "$new_report"

                pause_screen
                ;;

            3)
                echo
                echo "Available forensic snapshots:"
                echo
                python "$LAB/forensics/report_utils.py"
                echo
                read -rp "Report path: " report

                python "$LAB/forensics/timeline.py" "$report"

                pause_screen
                ;;

            4)
                clear
                python "$LAB/forensics/report_utils.py"
                pause_screen
                ;;

            5)
                clear
                echo "LATEST FORENSIC SNAPSHOT"
                echo "────────────────────────────────────────"
                echo

                python - <<'PY2'
from forensics.report_utils import latest_report

report = latest_report()

if report:
    print(report)
else:
    print("No forensic snapshots found.")
PY2

                pause_screen
                ;;

            b|B)
                return
                ;;

            *)
                echo "Invalid command."
                sleep 1
                ;;
        esac
    done
}

while true; do
    show_header

    echo "  1) SYSTEM STATUS"
    echo "  2) PROCESS WATCH"
    echo "  3) SYSTEM SCAN"
    echo "  4) DIGITAL FORENSICS"
    echo "  5) EXPERIMENTS"
    echo "  6) REPORTS"
    echo "  7) MODULE STATUS"
    echo "  8) LAB HEALTH"
    echo "  9) GIT STATUS"
    echo
    echo "  Q) EXIT"
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
            forensics_menu
            ;;

        5)
            clear
            echo "EXPERIMENTS"
            echo "────────────────────────────────────────"
            echo
            find "$LAB/experiments" \
                -maxdepth 1 \
                -type f \
                -printf '%f\n' \
                | sort
            pause_screen
            ;;

        6)
            clear
            echo "REPORTS"
            echo "────────────────────────────────────────"
            echo
            find "$LAB/reports" \
                -maxdepth 1 \
                -type f \
                -printf '%TY-%Tm-%Td %TH:%TM  %f\n' \
                | sort -r
            pause_screen
            ;;

        7)
            clear
            python "$LAB/mission_control/lab_status.py"
            pause_screen
            ;;

        8)
            python "$LAB/mission_control/lab_health.py"
            pause_screen
            ;;

        9)
            clear
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
            echo "Invalid command."
            sleep 1
            ;;
    esac
done
