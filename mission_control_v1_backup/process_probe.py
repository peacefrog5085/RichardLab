import psutil
import time
from datetime import datetime

THRESHOLD = 70.0

print("RICHARDLAB PROCESS WATCHER")
print("==========================")
print(f"Alert threshold: {THRESHOLD}% CPU")
print("Press Ctrl+C to stop.\n")

try:
    while True:
        timestamp = datetime.now().strftime("%H:%M:%S")

        processes = []

        for p in psutil.process_iter(
            ["pid", "name", "cpu_percent", "memory_percent"]
        ):
            try:
                info = p.info
                processes.append(info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        processes.sort(
            key=lambda x: x["cpu_percent"] or 0,
            reverse=True
        )

        top = processes[:5]

        print(f"\n{timestamp}")
        print("-" * 70)

        for p in top:
            cpu = p["cpu_percent"] or 0
            mem = p["memory_percent"] or 0

            marker = "  <== HIGH CPU" if cpu >= THRESHOLD else ""

            print(
                f"PID {p['pid']:>7} | "
                f"CPU {cpu:>5.1f}% | "
                f"RAM {mem:>5.1f}% | "
                f"{p['name']}{marker}"
            )

        time.sleep(2)

except KeyboardInterrupt:
    print("\nWatcher stopped.")
