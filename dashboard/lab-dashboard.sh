#!/usr/bin/env bash

clear

echo "╔══════════════════════════════════════════════════════╗"
echo "║              RICHARD DIGITAL LAB v0.1               ║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║                                                      ║"

HOSTNAME_NOW=$(hostname)
KERNEL=$(uname -r)
UPTIME=$(uptime -p)
CPU=$(nproc)

MEM_TOTAL=$(free -h | awk '/Mem:/ {print $2}')
MEM_USED=$(free -h | awk '/Mem:/ {print $3}')
MEM_PERCENT=$(free | awk '/Mem:/ {printf "%.1f", $3/$2*100}')

DISK=$(df -h "$HOME" | awk 'NR==2 {print $3 " used / " $2 " total (" $5 ")"}')

LOAD=$(awk '{print $1, $2, $3}' /proc/loadavg)

echo "║  SYSTEM"
echo "║  Host:       $HOSTNAME_NOW"
echo "║  Kernel:     $KERNEL"
echo "║  CPU cores:  $CPU"
echo "║  RAM:        $MEM_USED / $MEM_TOTAL ($MEM_PERCENT%)"
echo "║  Disk:       $DISK"
echo "║  Load:       $LOAD"
echo "║  Uptime:     $UPTIME"
echo "║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  LAB MODULES"
echo "║"
echo "║  [AI]          ~/RichardLab/ai"
echo "║  [FORENSICS]   ~/RichardLab/forensics"
echo "║  [VALUE FLOW]  ~/RichardLab/value_flow"
echo "║  [MEDIA]       ~/RichardLab/media"
echo "║  [EXPERIMENTS] ~/RichardLab/experiments"
echo "║  [KNOWLEDGE]   ~/RichardLab/knowledge"
echo "║"
echo "╠══════════════════════════════════════════════════════╣"
echo "║  STATUS: ONLINE"
echo "║  OWNER:  RICHARD"
echo "║                                                      ║"
echo "║       QUESTION EVERYTHING. VERIFY THE DATA.         ║"
echo "╚══════════════════════════════════════════════════════╝"

