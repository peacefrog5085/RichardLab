import tkinter as tk
import random
import math
import time

WIDTH = 1000
HEIGHT = 650
PARTICLES = 250

G = 0.035
FRICTION = 0.992
MAX_SPEED = 8

root = tk.Tk()
root.title("RichardLab Experiment #005 - Emergence")

canvas = tk.Canvas(
    root,
    width=WIDTH,
    height=HEIGHT,
    bg="black",
    highlightthickness=0
)

canvas.pack()

particles = []

for _ in range(PARTICLES):
    particles.append({
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, HEIGHT),
        "vx": random.uniform(-1, 1),
        "vy": random.uniform(-1, 1),
        "mass": random.uniform(0.5, 2.0)
    })


def update():
    for p in particles:

        fx = 0
        fy = 0

        for q in particles:

            if p is q:
                continue

            dx = q["x"] - p["x"]
            dy = q["y"] - p["y"]

            distance_sq = dx * dx + dy * dy

            if distance_sq < 25:
                distance_sq = 25

            distance = math.sqrt(distance_sq)

            force = G * q["mass"] / distance_sq

            fx += force * dx / distance
            fy += force * dy / distance

        p["vx"] += fx
        p["vy"] += fy

        p["vx"] *= FRICTION
        p["vy"] *= FRICTION

        speed = math.sqrt(
            p["vx"] ** 2 +
            p["vy"] ** 2
        )

        if speed > MAX_SPEED:
            p["vx"] *= MAX_SPEED / speed
            p["vy"] *= MAX_SPEED / speed

        p["x"] += p["vx"]
        p["y"] += p["vy"]

        if p["x"] < 0:
            p["x"] = WIDTH
        elif p["x"] > WIDTH:
            p["x"] = 0

        if p["y"] < 0:
            p["y"] = HEIGHT
        elif p["y"] > HEIGHT:
            p["y"] = 0


def draw():
    canvas.delete("all")

    for p in particles:

        x = p["x"]
        y = p["y"]

        size = 2 + p["mass"]

        canvas.create_oval(
            x - size,
            y - size,
            x + size,
            y + size,
            fill="white",
            outline=""
        )


def loop():
    start = time.perf_counter()

    update()
    draw()

    elapsed = time.perf_counter() - start

    fps = 1 / elapsed if elapsed > 0 else 0

    root.title(
        f"RichardLab Experiment #005 - "
        f"Particles: {PARTICLES} | "
        f"FPS: {fps:.1f}"
    )

    root.after(1, loop)


root.after(1, loop)

root.mainloop()
