import math
import tkinter as tk

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

all_trajectories = []
all_dts = []


def calculate_trajectory(height, angle, speed, size, weight, dt):
    g = 9.81
    c = 0.15
    rho = 1.29
    x = 0
    y = height
    a = angle * math.pi / 180
    vx = speed * math.cos(a)
    vy = speed * math.sin(a)
    k = 0.5 * c * rho * size / weight
    points = []
    max_y = y
    while y >= 0:
        v = math.sqrt(vx**2 + vy**2)
        vx -= k * vx * v * dt
        vy -= (g + k * vy * v) * dt
        x += vx * dt
        y += vy * dt
        if y > max_y:
            max_y = y
        if y >= 0:
            points.append((x, y))
    final_speed = math.sqrt(vx**2 + vy**2)
    return points, x, max_y, final_speed


def add_trajectory():
    try:
        height = float(entry_height.get())
        angle = float(entry_angle.get())
        speed = float(entry_speed.get())
        weight = float(entry_weight.get())
        size = float(entry_size.get())
        dt = float(entry_dt.get())
        trajectory, distance, max_height, final_speed = calculate_trajectory(
            height, angle, speed, size, weight, dt
        )
        all_trajectories.append(trajectory)
        all_dts.append(dt)
        metrics_label.config(
            text=f"Дальность: {distance:.3f} м\n"
            f"Макс. высота: {max_height:.3f} м\n"
            f"Скорость при падении: {final_speed:.3f} м/с"
        )
        draw_graph()
    except:
        pass


def clear_trajectories():
    all_trajectories.clear()
    all_dts.clear()
    metrics_label.config(text="")
    ax.cla()
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Траектории")
    ax.grid(True)
    canvas.draw()


def draw_graph():
    ax.cla()
    unique_dts = set()
    for traj, dt in zip(all_trajectories[:-1], all_dts[:-1]):
        xs, ys = zip(*traj)
        ax.plot(xs, ys, label=f"dt={dt}" if dt not in unique_dts else "")
        unique_dts.add(dt)
    if all_trajectories:
        last_traj = all_trajectories[-1]
        last_dt = all_dts[-1]
        xs, ys = zip(*last_traj)
        step = max(1, len(xs) // 50)
        for i in range(0, len(xs), step):
            label = (
                f"dt={last_dt}"
                if (i == 0 and last_dt not in unique_dts)
                else ""
            )
            ax.plot(xs[:i], ys[:i], label=label)
            canvas.draw()
            root.update()
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Траектории")
    ax.grid(True)
    if all_trajectories:
        ax.legend()
    canvas.draw()


root = tk.Tk()
root.title("Моделирование полёта тела в атмосфере")
root.geometry("1000x520")

left_frame = tk.Frame(root)
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

tk.Label(left_frame, text="Шаг моделирования, с:").pack()
entry_dt = tk.Entry(left_frame)
entry_dt.insert(0, "0.001")
entry_dt.pack()
tk.Label(left_frame, text="Высота, м:").pack()
entry_height = tk.Entry(left_frame)
entry_height.insert(0, "0")
entry_height.pack()
tk.Label(left_frame, text="Угол:").pack()
entry_angle = tk.Entry(left_frame)
entry_angle.insert(0, "10")
entry_angle.pack()
tk.Label(left_frame, text="Скорость, м/с:").pack()
entry_speed = tk.Entry(left_frame)
entry_speed.insert(0, "100")
entry_speed.pack()
tk.Label(left_frame, text="Масса, кг:").pack()
entry_weight = tk.Entry(left_frame)
entry_weight.insert(0, "10")
entry_weight.pack()
tk.Label(left_frame, text="Размер, м^2:").pack()
entry_size = tk.Entry(left_frame)
entry_size.insert(0, "0.2")
entry_size.pack()
tk.Button(left_frame, text="Добавить траекторию", command=add_trajectory).pack(
    pady=6
)
tk.Button(left_frame, text="Очистить", command=clear_trajectories).pack(pady=5)
metrics_label = tk.Label(
    left_frame, text="", justify=tk.CENTER, font=("Arial", 10)
)
metrics_label.pack(pady=10)

right_frame = tk.Frame(root)
right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

fig, ax = plt.subplots(figsize=(6, 4))
ax.set_xlabel("x")
ax.set_ylabel("y")
ax.set_title("Траектории")
ax.grid(True)

canvas = FigureCanvasTkAgg(fig, master=right_frame)
canvas.draw()
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

root.mainloop()
