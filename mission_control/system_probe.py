import psutil
import time
import csv
import os
from datetime import datetime

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "system_metrics.csv")

os.makedirs(DATA_DIR, exist_ok=True)

file_exists = os.path.exists(DATA_FILE)

with open(DATA_FILE, "a", newline="") as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow([
            "timestamp",
            "cpu_percent",
            "ram_percent",
            "swap_percent",
            "disk_percent"
        ])

    print("RICHARDLAB SYSTEM PROBE")
    print("=======================")
    print(f"Recording to: {DATA_FILE}")
    print("Press Ctrl+C to stop.\n")

    try:
        while True:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            disk = psutil.disk_usage("/")

            writer.writerow([
                timestamp,
                cpu,
                mem.percent,
                swap.percent,
                disk.percent
            ])

            f.flush()

            print(
                f"{timestamp} | "
                f"CPU {cpu:5.1f}% | "
                f"RAM {mem.percent:5.1f}% | "
                f"SWAP {swap.percent:5.1f}% | "
                f"DISK {disk.percent:5.1f}%"
            )

            time.sleep(2)

    except KeyboardInterrupt:
        print("\nProbe stopped.")
        print(f"Data saved to {DATA_FILE}")
