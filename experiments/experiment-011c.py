import tkinter as tk
import random
import math
import time
import csv
from datetime import datetime

WIDTH = 1000
HEIGHT = 700

POPULATION = 120

MUTATION_RATE = 0.08
GENERATION_TIME = 1.5

WORLD = "scarce"

WORLDS = {
    "abundant": {
        "food_count": 400,
        "moving": False
    },
    "scarce": {
        "food_count": 80,
        "moving": False
    },
    "moving": {
        "food_count": 100,
        "moving": True
    }
}

random.seed(1981)

root = tk.Tk()
root.title("RichardLab #011c - Evolution Lab")

canvas = tk.Canvas(
    root,
    width=WIDTH,
    height=HEIGHT,
    bg="black",
    highlightthickness=0
)

canvas.pack()

creatures = []
food = []

generation = 1
generation_start = time.time()
paused = False

report_file = (
    "/home/rich/RichardLab/reports/"
    f"experiment_011c_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.csv"
)

report = open(report_file, "w", newline="")

writer = csv.writer(report)

writer.writerow([
    "world",
    "generation",
    "population",
    "best_energy",
    "best_speed",
    "best_vision",
    "average_energy",
    "average_speed",
    "average_vision"
])


def new_creature():

    return {
        "x": random.uniform(20, WIDTH - 20),
        "y": random.uniform(20, HEIGHT - 20),
        "speed": random.uniform(0.5, 2.5),
        "vision": random.uniform(40, 150),
        "energy": 100,
        "size": random.uniform(2, 5)
    }


def new_food():

    count = WORLDS[WORLD]["food_count"]

    return [
        {
            "x": random.uniform(10, WIDTH - 10),
            "y": random.uniform(10, HEIGHT - 10),
            "vx": random.uniform(-0.7, 0.7),
            "vy": random.uniform(-0.7, 0.7)
        }
        for _ in range(count)
    ]


def reset():

    global creatures
    global food
    global generation
    global generation_start

    creatures = [
        new_creature()
        for _ in range(POPULATION)
    ]

    food = new_food()

    generation = 1
    generation_start = time.time()


reset()


def mutate(parent):

    child = parent.copy()

    if random.random() < MUTATION_RATE:
        child["speed"] += random.uniform(-0.35, 0.35)

    if random.random() < MUTATION_RATE:
        child["vision"] += random.uniform(-20, 20)

    if random.random() < MUTATION_RATE:
        child["size"] += random.uniform(-0.5, 0.5)

    child["speed"] = max(
        0.1,
        min(4, child["speed"])
    )

    child["vision"] = max(
        20,
        min(250, child["vision"])
    )

    child["size"] = max(
        1,
        min(8, child["size"])
    )

    child["x"] = random.uniform(20, WIDTH - 20)
    child["y"] = random.uniform(20, HEIGHT - 20)
    child["energy"] = 100

    return child


def evolve():

    global creatures
    global food
    global generation
    global generation_start

    survivors = [
        c for c in creatures
        if c["energy"] > 0
    ]

    if not survivors:
        reset()
        return

    survivors.sort(
        key=lambda c: c["energy"],
        reverse=True
    )

    best = survivors[0]

    average_energy = sum(
        c["energy"]
        for c in creatures
    ) / len(creatures)

    average_speed = sum(
        c["speed"]
        for c in creatures
    ) / len(creatures)

    average_vision = sum(
        c["vision"]
        for c in creatures
    ) / len(creatures)

    writer.writerow([
        WORLD,
        generation,
        len(creatures),
        round(best["energy"], 3),
        round(best["speed"], 3),
        round(best["vision"], 3),
        round(average_energy, 3),
        round(average_speed, 3),
        round(average_vision, 3)
    ])

    report.flush()

    survivors = survivors[
        :max(5, len(survivors) // 2)
    ]

    new_population = []

    while len(new_population) < POPULATION:

        parent = random.choice(survivors)

        child = mutate(parent)

        new_population.append(child)

    creatures = new_population

    food = new_food()

    generation += 1
    generation_start = time.time()


def update_food():

    if not WORLDS[WORLD]["moving"]:
        return

    for f in food:

        f["x"] += f["vx"]
        f["y"] += f["vy"]

        if f["x"] < 5 or f["x"] > WIDTH - 5:
            f["vx"] *= -1

        if f["y"] < 5 or f["y"] > HEIGHT - 5:
            f["vy"] *= -1


def update():

    if paused:
        return

    update_food()

    for c in creatures:

        target = None

        target_distance = c["vision"]

        for f in food:

            dx = f["x"] - c["x"]
            dy = f["y"] - c["y"]

            distance = math.sqrt(
                dx * dx +
                dy * dy
            )

            if distance < target_distance:

                target = f
                target_distance = distance

        if target:

            dx = target["x"] - c["x"]
            dy = target["y"] - c["y"]

            distance = math.sqrt(
                dx * dx +
                dy * dy
            )

            if distance > 0:

                c["x"] += (
                    dx /
                    distance *
                    c["speed"]
                )

                c["y"] += (
                    dy /
                    distance *
                    c["speed"]
                )

        else:

            c["x"] += random.uniform(
                -c["speed"],
                c["speed"]
            )

            c["y"] += random.uniform(
                -c["speed"],
                c["speed"]
            )

        c["energy"] -= (
            0.05 +
            c["speed"] * 0.015
        )

        for f in food:

            dx = f["x"] - c["x"]
            dy = f["y"] - c["y"]

            if dx * dx + dy * dy < 100:

                c["energy"] += 25

                f["x"] = random.uniform(
                    10,
                    WIDTH - 10
                )

                f["y"] = random.uniform(
                    10,
                    HEIGHT - 10
                )

                break

        c["x"] %= WIDTH
        c["y"] %= HEIGHT

    if (
        time.time() -
        generation_start >
        GENERATION_TIME
    ):

        evolve()


def draw():

    canvas.delete("all")

    for f in food:

        canvas.create_oval(
            f["x"] - 2,
            f["y"] - 2,
            f["x"] + 2,
            f["y"] + 2,
            fill="white",
            outline=""
        )

    for c in creatures:

        size = c["size"]

        canvas.create_oval(
            c["x"] - size,
            c["y"] - size,
            c["x"] + size,
            c["y"] + size,
            fill="white",
            outline=""
        )

    best = max(
        creatures,
        key=lambda c: c["energy"]
    )

    canvas.create_oval(
        best["x"] - 7,
        best["y"] - 7,
        best["x"] + 7,
        best["y"] + 7,
        outline="white"
    )

    status = (
        "PAUSED"
        if paused
        else "RUNNING"
    )

    canvas.create_text(
        15,
        15,
        anchor="nw",
        fill="white",
        text=(
            "RICHARDLAB #011c\n"
            "EVOLUTION LAB\n\n"
            f"World: {WORLD}\n"
            f"Generation: {generation}\n"
            f"Population: {len(creatures)}\n"
            f"Best energy: {best['energy']:.1f}\n"
            f"Best speed: {best['speed']:.2f}\n"
            f"Best vision: {best['vision']:.1f}\n"
            f"Status: {status}\n\n"
            "A = abundant\n"
            "S = scarce\n"
            "M = moving food\n"
            "R = reset\n"
            "SPACE = pause\n"
            "ESC = quit"
        )
    )


def set_world(world):

    global WORLD

    WORLD = world

    reset()


def pause(event=None):

    global paused

    paused = not paused


def quit_lab(event=None):

    report.flush()
    report.close()
    root.destroy()


def loop():

    update()
    draw()

    root.after(
        16,
        loop
    )


root.bind(
    "<space>",
    pause
)

root.bind(
    "r",
    lambda event: reset()
)

root.bind(
    "R",
    lambda event: reset()
)

root.bind(
    "a",
    lambda event: set_world("abundant")
)

root.bind(
    "A",
    lambda event: set_world("abundant")
)

root.bind(
    "s",
    lambda event: set_world("scarce")
)

root.bind(
    "S",
    lambda event: set_world("scarce")
)

root.bind(
    "m",
    lambda event: set_world("moving")
)

root.bind(
    "M",
    lambda event: set_world("moving")
)

root.bind(
    "<Escape>",
    quit_lab
)

root.protocol(
    "WM_DELETE_WINDOW",
    quit_lab
)

root.after(
    16,
    loop
)

root.mainloop()
