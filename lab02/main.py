import tkinter as tk
from tkinter import messagebox

import matplotlib

matplotlib.use("TkAgg")
import time

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


def simulate(h, tau, lam, pc, L, T0, T_left, T_right, t_end):
    N = int(L / h) + 1
    x = [i * h for i in range(N)]

    T = [T0] * N
    T[0] = T_left
    T[N - 1] = T_right

    A = lam / h**2
    C = lam / h**2
    B = 2 * lam / h**2 + pc / tau

    steps = int(t_end / tau)
    start_time = time.time()

    for _ in range(steps):
        F = [0.0] * N
        for i in range(1, N - 1):
            F[i] = -(pc / tau) * T[i]

        alpha = [0.0] * N
        beta = [0.0] * N
        alpha[1] = 0.0
        beta[1] = T_left

        for i in range(2, N - 1):
            alpha[i] = A / (B - C * alpha[i - 1])
            beta[i] = (C * beta[i - 1] - F[i]) / (B - C * alpha[i - 1])

        T_new = T[:]
        T_new[0] = T_left
        T_new[N - 1] = T_right

        for i in range(N - 2, 0, -1):
            T_new[i] = alpha[i] * T_new[i + 1] + beta[i]

        T = T_new

    elapsed = time.time() - start_time
    center_idx = N // 2
    T_center = T[center_idx]

    return T, x, T_center, elapsed


def run():
    try:
        h = float(entry_dx.get())
        tau = float(entry_dt.get())
        lam = float(entry_lam.get())
        pc = float(entry_p.get()) * float(entry_c.get())
        L = float(entry_L.get())
        T0 = float(entry_T0.get())
        T_left = float(entry_Tleft.get())
        T_right = float(entry_Tright.get())
        t_end = float(entry_tend.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Введите числа во все поля!")
        return

    T_final, x, T_center, elapsed = simulate(
        h, tau, lam, pc, L, T0, T_left, T_right, t_end
    )

    label_result.config(
        text=f"Температура в центре: {T_center:.4f} °C\nВремя расчёта: {elapsed:.4f} с",
        fg="red",
    )

    ax.clear()
    ax.plot(x, T_final, "b-", linewidth=2)
    ax.plot(L / 2, T_center, "ro", markersize=8)
    ax.annotate(
        f"{T_center:.2f} C",
        xy=(L / 2, T_center),
        xytext=(
            L / 2 + L * 0.03,
            T_center - (T0 - min(T_left, T_right)) * 0.04,
        ),
        fontsize=10,
        color="red",
    )
    ax.set_xlabel("x, м")
    ax.set_ylabel("T, C")
    ax.set_title(f"Распределение температуры в пластине (t = {t_end} с)")
    ax.grid(True)
    canvas.draw()


root = tk.Tk()
root.title("Лабораторная 2 — Теплопроводность (метод сеток)")
root.resizable(False, False)

frame_left = tk.Frame(root, padx=15, pady=15)
frame_left.pack(side=tk.LEFT, fill=tk.Y)

tk.Label(frame_left, text="Параметры", font=("Arial", 12, "bold")).grid(
    row=0, column=0, columnspan=2, pady=(0, 10)
)

fields = [
    ("Толщина пластины L, м:", "0.1"),
    ("Начальная температура T0, C:", "100"),
    ("Темп. левой границы Tл, C:", "0"),
    ("Темп. правой границы Tп, C:", "0"),
    ("Теплопроводность λ, Вт/(м * C):", "394"),
    ("Плотность тела ρ, кг / м^3", "8920"),
    ("Удельная теплоемкость c, Дж / (кг * C): ", "380"),
    ("Время моделирования t, с:", "2.0"),
    ("Шаг по пространству h, м:", "0.1"),
    ("Шаг по времени t, с:", "0.1"),
]

entries = []
for i, (text, default) in enumerate(fields):
    tk.Label(frame_left, text=text, anchor="w").grid(
        row=i + 1, column=0, sticky="w", pady=3
    )
    e = tk.Entry(frame_left, width=12)
    e.insert(0, default)
    e.grid(row=i + 1, column=1, padx=(10, 0), pady=3)
    entries.append(e)

(
    entry_L,
    entry_T0,
    entry_Tleft,
    entry_Tright,
    entry_lam,
    entry_p,
    entry_c,
    entry_tend,
    entry_dx,
    entry_dt,
) = entries

tk.Button(
    frame_left,
    text="Рассчитать",
    command=run,
    bg="#0078d7",
    fg="blue",
    font=("Arial", 11),
    padx=10,
    pady=5,
).grid(row=len(fields) + 1, column=0, columnspan=2, pady=15)

label_result = tk.Label(
    frame_left, text="", font=("Arial", 11), justify=tk.LEFT
)
label_result.grid(row=len(fields) + 2, column=0, columnspan=2)

frame_right = tk.Frame(root)
frame_right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

fig, ax = plt.subplots(figsize=(6, 4.5))
fig.tight_layout(pad=3)
canvas = FigureCanvasTkAgg(fig, master=frame_right)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

root.mainloop()
