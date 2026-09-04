#!/usr/bin/env bash

LAB="$HOME/RichardLab"

pause_screen() {
    echo
    read -rp "Press ENTER to return..."
}

while true; do
    clear

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                    EXPERIMENT CENTER                     ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo
    echo "  1) LIST EXPERIMENTS"
    echo "  2) INSPECT EXPERIMENT"
    echo "  3) LATEST EXPERIMENT"
    echo "  4) EXPERIMENT COUNT"
    echo "  5) RECENT EXPERIMENT ACTIVITY"
    echo "  6) VIEW EXPERIMENT RESULTS"
    echo "  7) INSPECT RESULT"
    echo
    echo "  B) BACK"
    echo

    read -rp "Select: " choice

    case "$choice" in
        1)
            clear
            echo "EXPERIMENTS"
            echo "────────────────────────────────────────────────────────────"
            echo
            find "$LAB/experiments" \
                -maxdepth 1 \
                -type f \
                \( -name "*.py" -o -name "*.sh" \) \
                -printf '%f\n' \
                | sort
            pause_screen
            ;;

        2)
            "$LAB/mission_control/inspect_experiment.sh"
            ;;

        3)
            clear
            echo "LATEST EXPERIMENT"
            echo "────────────────────────────────────────────────────────────"
            echo

            latest="$(find "$LAB/experiments" \
                -maxdepth 1 \
                -type f \
                \( -name "*.py" -o -name "*.sh" \) \
                -printf '%T@ %p\n' \
                | sort -nr \
                | head -n 1 \
                | cut -d' ' -f2-)"

            if [[ -n "$latest" ]]; then
                basename "$latest"
                echo
                stat -c "Modified : %y%nSize     : %s bytes" "$latest"
            else
                echo "No experiments found."
            fi

            pause_screen
            ;;

        4)
            clear
            echo "EXPERIMENT COUNT"
            echo "────────────────────────────────────────────────────────────"
            echo

            count="$(find "$LAB/experiments" \
                -maxdepth 1 \
                -type f \
                \( -name "*.py" -o -name "*.sh" \) \
                | wc -l)"

            echo "Registered experiment programs: $count"
            pause_screen
            ;;

        5)
            clear
            echo "RECENT EXPERIMENT ACTIVITY"
            echo "────────────────────────────────────────────────────────────"
            echo

            find "$LAB/experiments" \
                -maxdepth 1 \
                -type f \
                \( -name "*.py" -o -name "*.sh" \) \
                -printf '%T@|%TY-%Tm-%Td %TH:%TM:%TS|%f\n' \
                | sort -nr \
                | head -n 10 \
                | cut -d'|' -f2-

            pause_screen
            ;;

        6)
            clear
            echo "VIEW EXPERIMENT RESULTS"
            echo "────────────────────────────────────────────────────────────"
            echo
            echo "Available experiments:"
            echo

            find "$LAB/experiments" \
                -maxdepth 1 \
                -type f \
                \( -name "*.py" -o -name "*.sh" \) \
                -printf '%f\n' \
                | sort

            echo
            read -rp "Experiment filename: " experiment

            if [[ -z "$experiment" ]]; then
                echo "No experiment selected."
                pause_screen
                continue
            fi

            stem="${experiment%.*}"
            report_stem="${stem//-/_}"

            echo
            echo "RESULTS FOR: $experiment"
            echo "────────────────────────────────────────────────────────────"
            echo

            mapfile -t matches < <(find "$LAB/reports" -maxdepth 1 -type f -iname "*${report_stem}*" | sort)

            if [[ ${#matches[@]} -gt 0 ]]; then
                printf "%-34s %-8s %-12s %s\n" "FILE" "TYPE" "SIZE" "MODIFIED"
                printf "%-34s %-8s %-12s %s\n" "----------------------------------" "--------" "------------" "-------------------"

                for report in "${matches[@]}"; do
                    filename="$(basename "$report")"
                    type="${filename##*.}"
                    size="$(stat -c '%s' "$report")"
                    modified="$(stat -c '%y' "$report" | cut -d'.' -f1)"

                    case "${type,,}" in
                        png|jpg|jpeg|gif|webp)
                            category="IMAGE"
                            ;;
                        txt|md|log)
                            category="TEXT"
                            ;;
                        csv|json|tsv)
                            category="DATA"
                            ;;
                        *)
                            category="${type^^}"
                            ;;
                    esac

                    printf "%-34s %-8s %-12s %s\n"                         "$filename" "$category" "$size bytes" "$modified"
                done
            else
                echo "No report files found matching: $stem"
            fi

            pause_screen
            ;;

        7)
            "$LAB/mission_control/inspect_result.sh"
            ;;

        [bB])
            exit 0
            ;;

        *)
            echo
            echo "Invalid selection."
            sleep 1
            ;;
    esac
done
