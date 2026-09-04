#!/usr/bin/env bash

LAB="$HOME/RichardLab"

clear
echo "EXPERIMENT INSPECTOR"
echo "────────────────────────────────────────"
echo

find "$LAB/experiments" \
    -maxdepth 1 \
    -type f \
    \( -name 'experiment-*.py' -o -name 'experiment-*.sh' \) \
    -printf '%f\n' \
    | sort

echo
read -rp "Experiment filename: " experiment

if [[ -z "$experiment" ]]; then
    exit 0
fi

echo

python "$LAB/mission_control/experiment_inspector.py" "$experiment"

echo
read -rp "Press ENTER to return..."
