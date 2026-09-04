import csv
import glob
import os
import statistics
import matplotlib.pyplot as plt

REPORT_DIR = "/home/rich/RichardLab/reports"

files = glob.glob(
    os.path.join(
        REPORT_DIR,
        "experiment_011c_*.csv"
    )
)

if not files:
    print("No Experiment 011c CSV files found.")
    raise SystemExit(1)

records = []

for filename in files:

    print(f"Reading: {os.path.basename(filename)}")

    with open(filename, newline="") as f:

        reader = csv.DictReader(f)

        for row in reader:

            records.append({
                "world": row["world"],
                "generation": int(row["generation"]),
                "best_energy": float(row["best_energy"]),
                "best_speed": float(row["best_speed"]),
                "best_vision": float(row["best_vision"]),
                "average_energy": float(row["average_energy"]),
                "average_speed": float(row["average_speed"]),
                "average_vision": float(row["average_vision"])
            })


worlds = sorted(
    set(r["world"] for r in records)
)

print()
print("=" * 60)
print("RICHARDLAB #011d")
print("EVOLUTION DATA ANALYZER")
print("=" * 60)

for world in worlds:

    data = [
        r for r in records
        if r["world"] == world
    ]

    print()
    print(f"WORLD: {world.upper()}")
    print("-" * 60)

    if not data:
        continue

    first = data[0]
    last = data[-1]

    speed_change = (
        last["average_speed"]
        - first["average_speed"]
    )

    vision_change = (
        last["average_vision"]
        - first["average_vision"]
    )

    energy_change = (
        last["average_energy"]
        - first["average_energy"]
    )

    print(
        f"Generations: "
        f"{first['generation']} -> "
        f"{last['generation']}"
    )

    print(
        f"Average speed: "
        f"{first['average_speed']:.3f} -> "
        f"{last['average_speed']:.3f} "
        f"({speed_change:+.3f})"
    )

    print(
        f"Average vision: "
        f"{first['average_vision']:.3f} -> "
        f"{last['average_vision']:.3f} "
        f"({vision_change:+.3f})"
    )

    print(
        f"Average energy: "
        f"{first['average_energy']:.3f} -> "
        f"{last['average_energy']:.3f} "
        f"({energy_change:+.3f})"
    )


def graph_metric(metric, title, ylabel, filename):

    plt.figure(figsize=(10, 6))

    for world in worlds:

        data = [
            r for r in records
            if r["world"] == world
        ]

        data.sort(
            key=lambda r: r["generation"]
        )

        generations = [
            r["generation"]
            for r in data
        ]

        values = [
            r[metric]
            for r in data
        ]

        plt.plot(
            generations,
            values,
            marker="o",
            label=world
        )

    plt.title(title)
    plt.xlabel("Generation")
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.legend()

    output = os.path.join(
        REPORT_DIR,
        filename
    )

    plt.savefig(
        output,
        dpi=150,
        bbox_inches="tight"
    )

    plt.close()

    print(f"Saved graph: {output}")


graph_metric(
    "average_speed",
    "Evolution of Average Speed",
    "Average Speed",
    "experiment_011d_speed.png"
)

graph_metric(
    "average_vision",
    "Evolution of Average Vision",
    "Average Vision",
    "experiment_011d_vision.png"
)

graph_metric(
    "average_energy",
    "Evolution of Average Energy",
    "Average Energy",
    "experiment_011d_energy.png"
)

summary_file = os.path.join(
    REPORT_DIR,
    "experiment_011d_summary.txt"
)

with open(summary_file, "w") as f:

    f.write(
        "RICHARDLAB #011d - EVOLUTION ANALYSIS\n"
    )

    f.write("=" * 60 + "\n\n")

    f.write(
        f"CSV files analyzed: {len(files)}\n"
    )

    f.write(
        f"Total observations: {len(records)}\n\n"
    )

    for world in worlds:

        data = [
            r for r in records
            if r["world"] == world
        ]

        if not data:
            continue

        first = data[0]
        last = data[-1]

        f.write(
            f"WORLD: {world}\n"
        )

        f.write(
            f"Generations: "
            f"{first['generation']} -> "
            f"{last['generation']}\n"
        )

        f.write(
            f"Speed change: "
            f"{last['average_speed'] - first['average_speed']:+.3f}\n"
        )

        f.write(
            f"Vision change: "
            f"{last['average_vision'] - first['average_vision']:+.3f}\n"
        )

        f.write(
            f"Energy change: "
            f"{last['average_energy'] - first['average_energy']:+.3f}\n\n"
        )

print()
print("=" * 60)
print("ANALYSIS COMPLETE")
print("=" * 60)
print()
print(f"Summary: {summary_file}")
