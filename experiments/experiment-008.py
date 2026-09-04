import tkinter as tk
import random
import math
import time

WIDTH = 1000
HEIGHT = 650

PARTICLES = 250

G = 0.04
FRICTION = 0.994
MAX_SPEED = 7

MOUSE_GRAVITY = 0.20
MOUSE_RADIUS = 250

GRID_SIZE = 50
DENSITY_THRESHOLD = 8

ANALYSIS_INTERVAL = 30

random.seed(1981)

root = tk.Tk()
root.title("RichardLab #008 - Cluster Detection")

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

cluster_count = 0
largest_cluster = 0


def make_particle():

    return {
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, HEIGHT),
        "vx": random.uniform(-1, 1),
        "vy": random.uniform(-1, 1),
        "mass": random.uniform(0.5, 2.0),
        "trail": []
    }


def reset():

    global particles

    particles = [
        make_particle()
        for _ in range(PARTICLES)
    ]


reset()


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


def increase_gravity(event=None):

    global G

    G *= 1.15


def decrease_gravity(event=None):

    global G

    G /= 1.15


def update():

    if paused:
        return

    for p in particles:

        fx = 0.0
        fy = 0.0

        for q in particles:

            if p is q:
                continue

            dx = q["x"] - p["x"]
            dy = q["y"] - p["y"]

            distance_sq = dx * dx + dy * dy

            if distance_sq < 100:
                distance_sq = 100

            distance = math.sqrt(distance_sq)

            force = G * q["mass"] / distance_sq

            fx += force * dx / distance
            fy += force * dy / distance

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

            scale = MAX_SPEED / speed

            p["vx"] *= scale
            p["vy"] *= scale

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

        if len(p["trail"]) > 10:
            p["trail"].pop(0)


def detect_clusters():

    global cluster_count
    global largest_cluster

    grid = {}

    for p in particles:

        gx = int(p["x"] // GRID_SIZE)
        gy = int(p["y"] // GRID_SIZE)

        key = (gx, gy)

        grid[key] = grid.get(key, 0) + 1

    occupied = {
        key
        for key, count in grid.items()
        if count >= DENSITY_THRESHOLD
    }

    visited = set()

    clusters = []

    for start in occupied:

        if start in visited:
            continue

        stack = [start]
        visited.add(start)

        size = 0

        while stack:

            cell = stack.pop()
            size += grid[cell]

            x, y = cell

            neighbors = [
                (x + 1, y),
                (x - 1, y),
                (x, y + 1),
                (x, y - 1)
            ]

            for neighbor in neighbors:

                if (
                    neighbor in occupied
                    and neighbor not in visited
                ):

                    visited.add(neighbor)
                    stack.append(neighbor)

        clusters.append(size)

    cluster_count = len(clusters)

    largest_cluster = (
        max(clusters)
        if clusters
        else 0
    )


def draw():

    canvas.delete("all")

    for p in particles:

        trail = p["trail"]

        if len(trail) >= 2:

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

    status = "PAUSED" if paused else "RUNNING"

    canvas.create_text(
        10,
        10,
        anchor="nw",
        fill="white",
        text=(
            f"RICHARDLAB #008   {status}\n"
            f"Particles: {len(particles)}\n"
            f"Gravity: {G:.4f}\n"
            f"Clusters: {cluster_count}\n"
            f"Largest cluster: {largest_cluster}\n"
            f"↑ ↓ gravity   SPACE pause   R reset   ESC quit"
        )
    )


analysis_counter = 0


def loop():

    global analysis_counter

    update()
    draw()

    analysis_counter += 1

    if analysis_counter >= ANALYSIS_INTERVAL:

        detect_clusters()

        analysis_counter = 0

    root.after(10, loop)


def quit_lab(event=None):

    root.destroy()


root.bind_all("<Motion>", mouse_move)
root.bind_all("<Enter>", mouse_enter)
root.bind_all("<Leave>", mouse_leave)

root.bind("<space>", toggle_pause)
root.bind("<Up>", increase_gravity)
root.bind("<Down>", decrease_gravity)
root.bind("r", reset)
root.bind("R", reset)
root.bind("<Escape>", quit_lab)

root.protocol(
    "WM_DELETE_WINDOW",
    quit_lab
)

root.after(10, loop)

root.mainloop()
