#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REGISTRY="$LAB/data/experiment_runs.csv"
ARTIFACT_REGISTRY="$LAB/data/experiment_artifacts.csv"

pause_screen() {
    echo
    read -rp "Press ENTER to return..."
}

while true; do
    clear

    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                     RUN HISTORY                          ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo

    if [[ ! -f "$REGISTRY" ]]; then
        echo "No experiment run registry exists yet."
        pause_screen
        exit 0
    fi

    echo "  1) ALL RUNS"
    echo "  2) SUCCESSFUL RUNS"
    echo "  3) FAILED RUNS"
    echo "  4) RUN DETAILS"
    echo "  5) ARTIFACTS BY RUN"
    echo "  6) RUN STATISTICS"
    echo
    echo "  B) BACK"
    echo

    read -rp "Select: " choice

    case "$choice" in
        1)
            clear
            echo "ALL EXPERIMENT RUNS"
            echo "────────────────────────────────────────────────────────────────────"
            echo

            column -s, -t "$REGISTRY" 2>/dev/null || cat "$REGISTRY"
            pause_screen
            ;;

        2)
            clear
            echo "SUCCESSFUL RUNS"
            echo "────────────────────────────────────────────────────────────────────"
            echo

            awk -F, 'NR==1 || $7=="SUCCESS"' "$REGISTRY" \
                | column -s, -t 2>/dev/null

            pause_screen
            ;;

        3)
            clear
            echo "FAILED RUNS"
            echo "────────────────────────────────────────────────────────────────────"
            echo

            awk -F, 'NR==1 || $7=="FAILED"' "$REGISTRY" \
                | column -s, -t 2>/dev/null

            pause_screen
            ;;

        4)
            clear
            echo "RUN DETAILS"
            echo "────────────────────────────────────────────────────────────────────"
            echo

            tail -n +2 "$REGISTRY" | cut -d',' -f1 | sort -r

            echo
            read -rp "Run ID: " run_id

            if [[ -z "$run_id" ]]; then
                continue
            fi

            echo
            awk -F, -v id="$run_id" '
                NR==1 { header=$0; next }
                $1==id {
                    print "Run ID           : " $1
                    print "Experiment       : " $2
                    print "Start time       : " $3
                    print "End time         : " $4
                    print "Duration         : " $5 " seconds"
                    print "Exit status      : " $6
                    print "Result           : " $7
                    found=1
                }
                END {
                    if (!found)
                        print "Run not found."
                }
            ' "$REGISTRY"

            pause_screen
            ;;

        5)
            clear
            echo "ARTIFACTS BY RUN"
            echo "────────────────────────────────────────────────────────────────────"
            echo

            if [[ ! -f "$ARTIFACT_REGISTRY" ]]; then
                echo "No artifact registry exists yet."
                pause_screen
                continue
            fi

            tail -n +2 "$REGISTRY" | cut -d',' -f1 | sort -r

            echo
            read -rp "Run ID: " run_id

            if [[ -z "$run_id" ]]; then
                continue
            fi

            echo
            echo "ARTIFACTS FOR RUN: $run_id"
            echo "────────────────────────────────────────────────────────────────────"

            awk -F, -v id="$run_id" '
                NR==1 { next }
                $1==id {
                    printf "%-34s %-8s %-12s %s\n", $3, $4, $5 " bytes", $6
                    found=1
                }
                END {
                    if (!found)
                        print "No artifacts registered for this run."
                }
            ' "$ARTIFACT_REGISTRY"

            pause_screen
            ;;

        6)
            clear
            echo "RUN STATISTICS"
            echo "────────────────────────────────────────────────────────────────────"
            echo

            total=$(tail -n +2 "$REGISTRY" | wc -l)
            successful=$(awk -F, 'NR>1 && $7=="SUCCESS" {count++} END {print count+0}' "$REGISTRY")
            failed=$(awk -F, 'NR>1 && $7=="FAILED" {count++} END {print count+0}' "$REGISTRY")

            if [[ "$total" -gt 0 ]]; then
                avg=$(awk -F, 'NR>1 {sum += $5; count++} END {if(count) printf "%.2f", sum/count; else print "0.00"}' "$REGISTRY")
            else
                avg="0.00"
            fi

            echo "Total runs       : $total"
            echo "Successful runs  : $successful"
            echo "Failed runs      : $failed"
            echo "Average duration : ${avg}s"

            pause_screen
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
