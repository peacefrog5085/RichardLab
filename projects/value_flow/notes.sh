#!/usr/bin/env bash

LAB="$HOME/RichardLab"
DATA="$LAB/projects/value_flow/data"
NOTES="$DATA/notes.txt"

mkdir -p "$DATA"
touch "$NOTES"

add_note() {
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║                 ADD PROJECT NOTE                    ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo

    read -rp "Note title > " title

    if [ -z "$title" ]; then
        echo "Title cannot be empty."
        sleep 1
        return
    fi

    echo
    echo "Enter your note."
    echo "When finished, press CTRL+D."
    echo

    note=$(cat)

    {
        echo "============================================================"
        echo "DATE: $(date '+%Y-%m-%d %H:%M:%S')"
        echo "TITLE: $title"
        echo "------------------------------------------------------------"
        echo "$note"
        echo
    } >> "$NOTES"

    echo
    echo "✓ NOTE SAVED"
    echo
    read -rp "Press ENTER to continue..."
}

view_notes() {
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║                  PROJECT NOTES                     ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo

    if [ ! -s "$NOTES" ]; then
        echo "No notes recorded yet."
    else
        cat "$NOTES"
    fi

    echo
    read -rp "Press ENTER to continue..."
}

search_notes() {
    clear
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║                  SEARCH NOTES                      ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo

    if [ ! -s "$NOTES" ]; then
        echo "No notes recorded yet."
        read -rp "Press ENTER to continue..."
        return
    fi

    read -rp "Search > " term

    echo
    echo "SEARCH RESULTS"
    echo "──────────────────────────────────────────────────────────"
    echo

    grep -i -n -C 2 -- "$term" "$NOTES" || echo "No matches found."

    echo
    read -rp "Press ENTER to continue..."
}

while true; do
    clear

    echo "╔══════════════════════════════════════════════════════╗"
    echo "║              VALUE FLOW NOTES                       ║"
    echo "╠══════════════════════════════════════════════════════╣"
    echo "║  Persistent project knowledge base                  ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo

    echo "  [1] Add Note"
    echo "  [2] View Notes"
    echo "  [3] Search Notes"
    echo "  [0] Return"
    echo

    read -rp "NOTES > " choice

    case "$choice" in
        1)
            add_note
            ;;
        2)
            view_notes
            ;;
        3)
            search_notes
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
