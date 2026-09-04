#!/usr/bin/env bash

LAB="$HOME/RichardLab"

pause_screen() {
    echo
    read -rp "Press ENTER to return..."
}

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                     RESULT INSPECTOR                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo
echo "Available report files:"
echo

find "$LAB/reports" \
    -maxdepth 1 \
    -type f \
    -printf '%f\n' \
    | sort

echo
read -rp "Result filename: " result

if [[ -z "$result" ]]; then
    echo "No result selected."
    pause_screen
    exit 0
fi

target="$LAB/reports/$result"

if [[ ! -f "$target" ]]; then
    echo
    echo "ERROR: Result not found:"
    echo "$result"
    pause_screen
    exit 1
fi

filename="$(basename "$target")"
extension="${filename##*.}"
size="$(stat -c '%s' "$target")"
modified="$(stat -c '%y' "$target" | cut -d'.' -f1)"
sha256="$(sha256sum "$target" | awk '{print $1}')"

case "${extension,,}" in
    txt|md|log)
        type="TEXT"
        ;;
    json)
        type="JSON"
        ;;
    csv)
        type="CSV"
        ;;
    png|jpg|jpeg|gif|webp)
        type="IMAGE"
        ;;
    *)
        type="${extension^^}"
        ;;
esac

clear
echo "RESULT INSPECTOR"
echo "════════════════════════════════════════════════════════════════════"
echo "Result     : $filename"
echo "Type       : $type"
echo "Size       : $size bytes"
echo "Modified   : $modified"
echo "SHA-256    : $sha256"
echo

case "${extension,,}" in
    txt|md|log)
        echo "CONTENT"
        echo "────────────────────────────────────────────────────────────────────"
        echo
        cat "$target"
        ;;

    json)
        echo "CONTENT"
        echo "────────────────────────────────────────────────────────────────────"
        echo
        if command -v python3 >/dev/null 2>&1; then
            python3 -m json.tool "$target" 2>/dev/null || cat "$target"
        else
            cat "$target"
        fi
        ;;

    csv)
        echo "CONTENT"
        echo "────────────────────────────────────────────────────────────────────"
        echo
        cat "$target"
        ;;

    png|jpg|jpeg|gif|webp)
        echo "IMAGE OUTPUT"
        echo "────────────────────────────────────────────────────────────────────"
        echo

        if command -v file >/dev/null 2>&1; then
            file "$target"
        fi

        if command -v identify >/dev/null 2>&1; then
            identify "$target" 2>/dev/null
        else
            echo "ImageMagick 'identify' not installed."
            echo "Basic file metadata shown above."
        fi
        ;;

    *)
        echo "BINARY / UNSUPPORTED OUTPUT"
        echo "────────────────────────────────────────────────────────────────────"
        echo
        echo "Content preview is disabled for this file type."
        echo "File metadata and SHA-256 are shown above."
        ;;
esac

echo
echo "INSPECTION COMPLETE"
pause_screen
