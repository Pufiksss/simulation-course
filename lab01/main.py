import math
import time
import tkinter as tk

import matplotlib.pyplot as plt

plt.ion()

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
    draw_graph()


def draw_graph():
    plt.clf()
    for traj, dt in zip(all_trajectories, all_dts):
        xs, ys = zip(*traj)
        for i in range(0, len(xs), 50):
            plt.plot(
                xs[:i],
                ys[:i],
                label=f"dt={dt}" if i == len(xs) - 5 else "",
            )
            plt.pause(0.0001)

    plt.xlabel("x")
    plt.ylabel("y")
    plt.title("Траектории")
    plt.grid(True)
    if all_trajectories:
        plt.legend()


root = tk.Tk()
root.title("Моделирование полёта тела в атмосфере")
root.geometry("520x520")

tk.Label(root, text="Шаг моделирования, с:").pack()
entry_dt = tk.Entry(root)
entry_dt.insert(0, "0.001")
entry_dt.pack()

tk.Label(root, text="Высота, м:").pack()
entry_height = tk.Entry(root)
entry_height.insert(0, "0")
entry_height.pack()

tk.Label(root, text="Угол:").pack()
entry_angle = tk.Entry(root)
entry_angle.insert(0, "10")
entry_angle.pack()

tk.Label(root, text="Скорость, м/с:").pack()
entry_speed = tk.Entry(root)
entry_speed.insert(0, "100")
entry_speed.pack()

tk.Label(root, text="Масса, кг:").pack()
entry_weight = tk.Entry(root)
entry_weight.insert(0, "10")
entry_weight.pack()

tk.Label(root, text="Размер, м^2:").pack()
entry_size = tk.Entry(root)
entry_size.insert(0, "0.2")
entry_size.pack()

tk.Button(root, text="Добавить траекторию", command=add_trajectory).pack(pady=6)
tk.Button(root, text="Очистить", command=clear_trajectories).pack(pady=5)

metrics_label = tk.Label(root, text="", justify=tk.CENTER, font=("Arial", 10))
metrics_label.pack(pady=10)

root.mainloop()
