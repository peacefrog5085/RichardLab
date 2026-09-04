#!/usr/bin/env bash

LAB="$HOME/RichardLab"
REPORT="$LAB/reports/experiment_004_$(date '+%Y-%m-%d_%H-%M-%S').txt"

mkdir -p "$LAB/reports"

{
echo "============================================================"
echo "          RICHARD DIGITAL LAB"
echo "          EXPERIMENT #004"
echo "          GPU / OPENGL CAPABILITY TEST"
echo "============================================================"
echo
echo "Date: $(date)"
echo

echo "---------------- GPU ----------------"

if command -v lspci >/dev/null 2>&1; then
    lspci | grep -Ei 'VGA|3D|Display'
fi

echo

echo "---------------- OPENGL ----------------"

if command -v glxinfo >/dev/null 2>&1; then
    glxinfo -B
else
    echo "glxinfo unavailable"
fi

echo

echo "---------------- DRM DEVICES ----------------"

ls -l /dev/dri/ 2>/dev/null || echo "No DRM devices found."

echo

echo "---------------- RENDER TEST ----------------"

if command -v glxgears >/dev/null 2>&1; then

    echo "Running 10-second OpenGL renderer test..."
    echo

    timeout 12s glxgears 2>&1 | head -n 8

else

    echo "glxgears is not installed."
    echo
    echo "No renderer benchmark performed."

fi

echo

echo "============================================================"
echo "EXPERIMENT COMPLETE"
echo "============================================================"

} | tee "$REPORT"

echo
echo "Report saved:"
echo "$REPORT"
