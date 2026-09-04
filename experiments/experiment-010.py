import tkinter as tk
import math
import random
import colorsys
import time

WIDTH = 1000
HEIGHT = 700

SEGMENTS = 12
POINTS = 120
TRAIL_LENGTH = 18

ROTATION = 0.004
ZOOM = 1.0

random.seed(1981)

root = tk.Tk()
root.title("RichardLab #010 - Kaleidoscope")

canvas = tk.Canvas(
    root,
    width=WIDTH,
    height=HEIGHT,
    bg="black",
    highlightthickness=0
)

canvas.pack()

cx = WIDTH / 2
cy = HEIGHT / 2

paused = False
hue_shift = 0.0

points = []

for _ in range(POINTS):

    angle = random.uniform(0, math.pi * 2)
    radius = random.uniform(20, min(WIDTH, HEIGHT) * 0.45)

    points.append({
        "angle": angle,
        "radius": radius,
        "speed": random.uniform(-0.008, 0.008),
        "pulse": random.uniform(0.01, 0.04),
        "size": random.uniform(1.0, 3.0),
        "hue": random.random(),
        "trail": []
    })


def hsv_color(h, s=1.0, v=1.0):

    r, g, b = colorsys.hsv_to_rgb(
        h % 1.0,
        s,
        v
    )

    return "#{:02x}{:02x}{:02x}".format(
        int(r * 255),
        int(g * 255),
        int(b * 255)
    )


def update():

    if paused:
        return

    global hue_shift

    hue_shift += 0.001

    for p in points:

        p["angle"] += p["speed"]

        p["radius"] += math.sin(
            time.perf_counter() * p["pulse"] * 20
        ) * 0.15

        x = math.cos(p["angle"]) * p["radius"]
        y = math.sin(p["angle"]) * p["radius"]

        p["trail"].append((x, y))

        if len(p["trail"]) > TRAIL_LENGTH:
            p["trail"].pop(0)


def draw():

    canvas.delete("all")

    segment_angle = (math.pi * 2) / SEGMENTS

    for p in points:

        trail = p["trail"]

        if len(trail) < 2:
            continue

        for segment in range(SEGMENTS):

            base_angle = segment * segment_angle

            for mirror in (1, -1):

                transformed = []

                for x, y in trail:

                    angle = math.atan2(y, x)
                    radius = math.sqrt(x * x + y * y)

                    new_angle = (
                        angle * mirror
                        + base_angle
                        + ZOOM * 0
                    )

                    tx = math.cos(new_angle) * radius
                    ty = math.sin(new_angle) * radius

                    transformed.append(
                        (
                            cx + tx,
                            cy + ty
                        )
                    )

                color = hsv_color(
                    p["hue"] + hue_shift + segment / SEGMENTS,
                    0.9,
                    1.0
                )

                canvas.create_line(
                    transformed,
                    fill=color,
                    width=p["size"],
                    smooth=True
                )

        # Bright center point
        x, y = trail[-1]

        for segment in range(SEGMENTS):

            base_angle = segment * segment_angle

            for mirror in (1, -1):

                angle = (
                    math.atan2(y, x) * mirror
                    + base_angle
                )

                radius = math.sqrt(
                    x * x + y * y
                )

                px = cx + math.cos(angle) * radius
                py = cy + math.sin(angle) * radius

                size = p["size"] + 1

                canvas.create_oval(
                    px - size,
                    py - size,
                    px + size,
                    py + size,
                    fill=hsv_color(
                        p["hue"] + hue_shift,
                        0.8,
                        1.0
                    ),
                    outline=""
                )

    # Center ring
    canvas.create_oval(
        cx - 8,
        cy - 8,
        cx + 8,
        cy + 8,
        outline="white"
    )

    status = "PAUSED" if paused else "RUNNING"

    canvas.create_text(
        15,
        15,
        anchor="nw",
        fill="white",
        text=(
            f"RICHARDLAB #010\n"
            f"KALEIDOSCOPE\n\n"
            f"Segments: {SEGMENTS}\n"
            f"Points: {POINTS}\n"
            f"Status: {status}\n\n"
            f"+ / -   symmetry\n"
            f"↑ / ↓   rotation\n"
            f"SPACE   pause\n"
            f"R       reset\n"
            f"ESC     quit"
        )
    )


def change_segments(amount):

    global SEGMENTS

    SEGMENTS += amount

    SEGMENTS = max(2, min(24, SEGMENTS))


def change_rotation(amount):

    global ROTATION

    ROTATION += amount


def toggle_pause(event=None):

    global paused

    paused = not paused


def reset(event=None):

    global hue_shift

    hue_shift = 0

    for p in points:

        p["angle"] = random.uniform(
            0,
            math.pi * 2
        )

        p["radius"] = random.uniform(
            20,
            min(WIDTH, HEIGHT) * 0.45
        )

        p["trail"].clear()


def quit_lab(event=None):

    root.destroy()


root.bind("+", lambda e: change_segments(1))
root.bind("=", lambda e: change_segments(1))
root.bind("-", lambda e: change_segments(-1))

root.bind("<Up>", lambda e: change_rotation(0.001))
root.bind("<Down>", lambda e: change_rotation(-0.001))

root.bind("<space>", toggle_pause)
root.bind("r", reset)
root.bind("R", reset)
root.bind("<Escape>", quit_lab)

root.protocol(
    "WM_DELETE_WINDOW",
    quit_lab
)


last_time = time.perf_counter()


def loop():

    global last_time

    start = time.perf_counter()

    update()
    draw()

    now = time.perf_counter()

    frame_time = now - last_time

    fps = (
        1 / frame_time
        if frame_time > 0
        else 0
    )

    last_time = now

    root.title(
        f"RichardLab #010 - Kaleidoscope | "
        f"{SEGMENTS} segments | "
        f"{fps:.1f} FPS"
    )

    root.after(16, loop)


root.after(16, loop)

root.mainloop()
