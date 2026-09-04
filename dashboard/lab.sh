#!/usr/bin/env bash

LAB="$HOME/RichardLab"

while true; do
    clear

    echo "╔══════════════════════════════════════════════════════╗"
    echo "║              RICHARD DIGITAL LAB                    ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║                                                      ║"
    echo "║   1) SYSTEM SCANNER                                  ║"
    echo "║   2) AI LAB                                          ║"
    echo "║   3) DIGITAL FORENSICS                               ║"
    echo "║   4) VALUE FLOW PROJECT                              ║"
    echo "║   5) EXPERIMENTS                                     ║"
    echo "║   6) MEDIA LAB                                       ║"
    echo "║   7) KNOWLEDGE BASE                                  ║"
    echo "║                                                      ║"
    echo "║   Q) EXIT                                            ║"
    echo "║                                                      ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo

    read -rp "RICHARD@LAB > " choice

    case "$choice" in

        1)
            "$LAB/dashboard/lab-dashboard.sh"
            read -rp "Press ENTER to return..."
            ;;

        2)
            clear
            echo "╔══════════════════════════════════════╗"
            echo "║              AI LAB                 ║"
            echo "╚══════════════════════════════════════╝"
            echo
            echo "AI workspace:"
            echo "$LAB/ai"
            echo
            echo "Local AI systems will live here."
            read -rp "Press ENTER to return..."
            ;;

        3)
            clear
            echo "╔══════════════════════════════════════╗"
            echo "║          DIGITAL FORENSICS           ║"
            echo "╚══════════════════════════════════════╝"
            echo
            echo "Evidence workspace:"
            echo "$LAB/forensics"
            echo
            echo "Metadata, hashes, timelines and file analysis."
            read -rp "Press ENTER to return..."
            ;;

        4)
            clear
            echo "╔══════════════════════════════════════╗"
            echo "║            VALUE FLOW                ║"
            echo "╚══════════════════════════════════════╝"
            echo
            echo "Workspace:"
            echo "$LAB/value_flow"
            echo
            echo "Economic relationships and value movement."
            read -rp "Press ENTER to return..."
            ;;

        5)
            clear
            echo "╔══════════════════════════════════════╗"
            echo "║             EXPERIMENTS              ║"
            echo "╚══════════════════════════════════════╝"
            echo
            echo "This is where the weird shit goes."
            echo
            echo "No assumptions."
            echo "No sacred cows."
            echo "Just hypotheses → experiments → results."
            read -rp "Press ENTER to return..."
            ;;

        6)
            clear
            echo "╔══════════════════════════════════════╗"
            echo "║              MEDIA LAB               ║"
            echo "╚══════════════════════════════════════╝"
            echo
            echo "OBS / FFmpeg / Kdenlive workspace."
            read -rp "Press ENTER to return..."
            ;;

        7)
            clear
            echo "╔══════════════════════════════════════╗"
            echo "║            KNOWLEDGE BASE            ║"
            echo "╚══════════════════════════════════════╝"
            echo
            echo "Research notes and discoveries:"
            echo "$LAB/knowledge"
            read -rp "Press ENTER to return..."
            ;;

        q|Q)
            clear
            echo "RICHARD DIGITAL LAB: OFFLINE"
            exit 0
            ;;

        *)
            echo
            echo "Invalid command. Even computers require us to read menus."
            sleep 1
            ;;
    esac
done
