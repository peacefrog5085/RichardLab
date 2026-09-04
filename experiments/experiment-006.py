import tkinter as tk
import random
import math
import time

WIDTH = 1000
HEIGHT = 650
PARTICLES = 300

G = 0.035
FRICTION = 0.992
MAX_SPEED = 8

MOUSE_GRAVITY = 0.15
MOUSE_RADIUS = 250

root = tk.Tk()
root.title("RichardLab Experiment #006 - Emergence")

canvas = tk.Canvas(
    root,
    width=WIDTH,
    height=HEIGHT,
    bg="black",
    highlightthickness=0
)

canvas.pack()

particles = []

mouse_x = WIDTH / 2
mouse_y = HEIGHT / 2
mouse_active = False

paused = False


for _ in range(PARTICLES):
    particles.append({
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, HEIGHT),
        "vx": random.uniform(-1, 1),
        "vy": random.uniform(-1, 1),
        "mass": random.uniform(0.5, 2.0),
        "trail": []
    })


def mouse_move(event):
    global mouse_x, mouse_y

    mouse_x = event.x
    mouse_y = event.y


def mouse_enter(event):
    global mouse_active
    mouse_active = True


def mouse_leave(event):
    global mouse_active
    mouse_active = False


def toggle_pause(event=None):
    global paused
    paused = not paused


def reset(event=None):
    for p in particles:
        p["x"] = random.uniform(0, WIDTH)
        p["y"] = random.uniform(0, HEIGHT)
        p["vx"] = random.uniform(-1, 1)
        p["vy"] = random.uniform(-1, 1)
        p["trail"].clear()


def update():
    if paused:
        return

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

        # Mouse becomes a temporary gravity well.
        if mouse_active:

            dx = mouse_x - p["x"]
            dy = mouse_y - p["y"]

            distance_sq = dx * dx + dy * dy

            if distance_sq < MOUSE_RADIUS ** 2:

                distance = math.sqrt(
                    max(distance_sq, 25)
                )

                force = MOUSE_GRAVITY / distance_sq

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

        p["trail"].append(
            (p["x"], p["y"])
        )

        if len(p["trail"]) > 12:
            p["trail"].pop(0)


def draw():

    canvas.delete("all")

    for p in particles:

        trail = p["trail"]

        if len(trail) > 1:

            canvas.create_line(
                trail,
                fill="gray",
                width=1
            )

        speed = math.sqrt(
            p["vx"] ** 2 +
            p["vy"] ** 2
        )

        size = 1.5 + p["mass"] + speed * 0.15

        canvas.create_oval(
            p["x"] - size,
            p["y"] - size,
            p["x"] + size,
            p["y"] + size,
            fill="white",
            outline=""
        )

    if mouse_active:

        canvas.create_oval(
            mouse_x - MOUSE_RADIUS,
            mouse_y - MOUSE_RADIUS,
            mouse_x + MOUSE_RADIUS,
            mouse_y + MOUSE_RADIUS,
            outline="gray"
        )

        canvas.create_oval(
            mouse_x - 5,
            mouse_y - 5,
            mouse_x + 5,
            mouse_y + 5,
            fill="white",
            outline=""
        )


def loop():

    start = time.perf_counter()

    update()
    draw()

    elapsed = time.perf_counter() - start

    fps = 1 / elapsed if elapsed > 0 else 0

    status = "PAUSED" if paused else "RUNNING"

    root.title(
        f"RichardLab #006 | "
        f"{status} | "
        f"Particles: {PARTICLES} | "
        f"FPS: {fps:.1f}"
    )

    root.after(1, loop)


canvas.bind("<Motion>", mouse_move)
canvas.bind("<Enter>", mouse_enter)
canvas.bind("<Leave>", mouse_leave)

root.bind("<space>", toggle_pause)
root.bind("<r>", reset)

root.after(1, loop)

root.mainloop()
