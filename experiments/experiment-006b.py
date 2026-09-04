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

root = tk.Tk()
root.title("RichardLab #006b - Emergence")

canvas = tk.Canvas(
    root,
    width=WIDTH,
    height=HEIGHT,
    bg="black",
    highlightthickness=0
)

canvas.pack()

# -----------------------------
# Particle creation
# -----------------------------

particles = []

for _ in range(PARTICLES):
    particles.append([
        random.uniform(0, WIDTH),
        random.uniform(0, HEIGHT),
        random.uniform(-1, 1),
        random.uniform(-1, 1),
        random.uniform(0.5, 2.0)
    ])


# -----------------------------
# Mouse gravity
# -----------------------------

mouse_x = WIDTH / 2
mouse_y = HEIGHT / 2
mouse_active = False


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


# -----------------------------
# Physics
# -----------------------------

def update():

    for p in particles:

        x, y, vx, vy, mass = p

        fx = 0.0
        fy = 0.0

        for q in particles:

            if p is q:
                continue

            dx = q[0] - x
            dy = q[1] - y

            dist_sq = dx * dx + dy * dy

            if dist_sq < 100:
                dist_sq = 100

            dist = math.sqrt(dist_sq)

            force = G * q[4] / dist_sq

            fx += force * dx / dist
            fy += force * dy / dist

        # Mouse gravity well
        if mouse_active:

            dx = mouse_x - x
            dy = mouse_y - y

            dist_sq = dx * dx + dy * dy

            if dist_sq > 25:

                dist = math.sqrt(dist_sq)

                force = 0.20 / dist_sq

                fx += force * dx / dist
                fy += force * dy / dist

        vx += fx
        vy += fy

        vx *= FRICTION
        vy *= FRICTION

        speed = math.sqrt(vx * vx + vy * vy)

        if speed > MAX_SPEED:

            scale = MAX_SPEED / speed

            vx *= scale
            vy *= scale

        x += vx
        y += vy

        # Wrap around edges
        if x < 0:
            x = WIDTH

        if x > WIDTH:
            x = 0

        if y < 0:
            y = HEIGHT

        if y > HEIGHT:
            y = 0

        p[0] = x
        p[1] = y
        p[2] = vx
        p[3] = vy


# -----------------------------
# Rendering
# -----------------------------

last_frame = time.perf_counter()


def draw():

    global last_frame

    canvas.delete("all")

    for p in particles:

        x, y, vx, vy, mass = p

        speed = math.sqrt(vx * vx + vy * vy)

        size = 1.5 + mass + speed * 0.15

        canvas.create_oval(
            x - size,
            y - size,
            x + size,
            y + size,
            fill="white",
            outline=""
        )

    now = time.perf_counter()

    elapsed = now - last_frame

    if elapsed > 0:
        fps = 1 / elapsed
    else:
        fps = 0

    last_frame = now

    root.title(
        f"RichardLab #006b | "
        f"Particles: {PARTICLES} | "
        f"FPS: {fps:.1f}"
    )


# -----------------------------
# Main loop
# -----------------------------

def loop():

    update()
    draw()

    root.after(10, loop)


# -----------------------------
# Quit controls
# -----------------------------

def quit_lab(event=None):
    root.destroy()


root.bind("<Escape>", quit_lab)

quit_button = tk.Button(
    root,
    text="QUIT EXPERIMENT",
    command=quit_lab
)

quit_button.pack(pady=5)

canvas.bind_all("<Motion>", mouse_move)
canvas.bind_all("<Enter>", mouse_enter)
canvas.bind_all("<Leave>", mouse_leave)

root.protocol("WM_DELETE_WINDOW", quit_lab)

root.after(10, loop)

root.mainloop()
