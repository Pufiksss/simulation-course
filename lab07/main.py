import math
import random
import tkinter as tk
from tkinter import ttk

import matplotlib
import numpy as np

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

STATE_NAMES = ["ясно", "облачно", "пасмурно"]
STATE_COLORS = ["#FFD54F", "#B0BEC5", "#607D8B"]

Q = [
    [-0.4, 0.3, 0.1],  # из "ясно"
    [0.4, -0.8, 0.4],  # из "облачно"
    [0.1, 0.4, -0.5],  # из "пасмурно"
]

N = 3


def base_random():
    a = random.random()
    while a <= 0.0:
        a = random.random()
    return a


def generate_dsv(probs):
    alpha = base_random()
    accumulated = 0.0
    for j in range(len(probs)):
        accumulated += probs[j]
        if alpha < accumulated:
            return j
    return len(probs) - 1


# вычисляет вероятности перехода
def transition_probs(i):
    q_ii = Q[i][i]
    probs = []
    for j in range(N):
        if j == i:
            probs.append(0.0)
        else:
            probs.append(-Q[i][j] / q_ii)
    return probs


def next_event(i):
    alpha = base_random()
    tau = math.log(alpha) / Q[i][i]
    j = generate_dsv(transition_probs(i))
    return tau, j


def stationary_theory():
    A = np.array(Q, dtype=float).T  # pi*Q = 0  <=>  Q^T * pi^T = 0
    A = np.vstack([A, np.ones(N)])  # дописываем условие нормировки
    b = np.zeros(N + 1)
    b[-1] = 1.0
    pi, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
    return list(pi)


TICK_MS = 50
REDRAW_EVERY = 4


class App:
    def __init__(self, root):
        self.root = root
        root.title("Имитационное моделирование марковской модели погоды")
        root.geometry("1150x800")

        self.theory = stationary_theory()
        self.running = False
        self.after_id = None
        self.tick_counter = 0

        self.build_interface()
        self.reset_model()
        self.update_all()

    def build_interface(self):
        self.status = tk.Label(
            self.root,
            text="",
            font=("Arial", 20, "bold"),
            height=2,
            relief="ridge",
            bd=2,
        )
        self.status.pack(fill="x", padx=8, pady=(8, 4))

        table_box = ttk.LabelFrame(
            self.root, text="Статистическая обработка", padding=6
        )
        table_box.pack(side="bottom", fill="x", padx=8, pady=8)

        middle = ttk.Frame(self.root)
        middle.pack(fill="both", expand=True, padx=8)

        panel = ttk.LabelFrame(middle, text="Управление", padding=10)
        panel.pack(side="left", fill="y", padx=(0, 8))

        ttk.Label(panel, text="Начальное состояние:").pack(anchor="w")
        self.start_state = ttk.Combobox(
            panel,
            width=18,
            state="readonly",
            values=["1 - ясно", "2 - облачно", "3 - пасмурно"],
        )
        self.start_state.current(0)
        self.start_state.pack(anchor="w", pady=(0, 10))

        ttk.Label(panel, text="Скорость, дней в секунду:").pack(anchor="w")
        self.speed = tk.DoubleVar(value=2.0)
        ttk.Scale(
            panel,
            from_=0.5,
            to=60.0,
            variable=self.speed,
            orient="horizontal",
            length=180,
            command=self.on_speed,
        ).pack(anchor="w")
        self.speed_label = ttk.Label(panel, text="2.0")
        self.speed_label.pack(anchor="w", pady=(0, 10))

        self.btn_start = ttk.Button(panel, text="Старт", command=self.start)
        self.btn_start.pack(fill="x", pady=2)
        self.btn_pause = ttk.Button(
            panel, text="Пауза", command=self.pause, state="disabled"
        )
        self.btn_pause.pack(fill="x", pady=2)
        ttk.Button(panel, text="Сброс", command=self.reset).pack(
            fill="x", pady=2
        )

        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=10)

        box = ttk.LabelFrame(panel, text="Матрица интенсивностей Q", padding=6)
        box.pack(fill="x")
        for i in range(N):
            ttk.Label(
                box,
                font=("Consolas", 9),
                text=" ".join("%6.1f" % Q[i][j] for j in range(N)),
            ).pack(anchor="w")

        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=10)

        self.lbl_time = ttk.Label(panel, text="")
        self.lbl_time.pack(anchor="w")
        self.lbl_steps = ttk.Label(panel, text="")
        self.lbl_steps.pack(anchor="w")

        self.fig = plt.Figure(figsize=(8, 5.0), dpi=95)
        self.ax_tr = self.fig.add_subplot(2, 1, 1)
        self.ax_bar = self.fig.add_subplot(2, 1, 2)
        self.fig.subplots_adjust(
            left=0.16, right=0.97, top=0.92, bottom=0.10, hspace=0.5
        )
        self.canvas = FigureCanvasTkAgg(self.fig, master=middle)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

        cols = ("state", "dur", "emp", "theory", "err")
        titles = {
            "state": "Состояние",
            "dur": "Время пребывания, дней",
            "emp": "Эмпирическая вероятность",
            "theory": "Теоретическая вероятность",
            "err": "Ошибка",
        }
        self.table = ttk.Treeview(
            table_box, columns=cols, show="headings", height=3
        )
        for c in cols:
            self.table.heading(c, text=titles[c])
            self.table.column(c, anchor="center", width=190)
        self.table.pack(fill="x")
        for i in range(N):
            self.table.insert(
                "", "end", iid=str(i), values=("", "", "", "", "")
            )

    def reset_model(self):
        self.t = 0.0
        self.i = self.start_state.current()
        tau, self.j_next = next_event(self.i)
        self.t_next = self.t + tau
        self.traj = [(0.0, self.i)]
        self.dur = [0.0] * N
        self.steps = 0

    def on_speed(self, _value):
        self.speed_label.config(text="%.1f" % self.speed.get())

    def start(self):
        if self.running:
            return
        self.running = True
        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.tick()

    def pause(self):
        self.running = False
        self.btn_start.config(state="normal")
        self.btn_pause.config(state="disabled")
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def reset(self):
        self.pause()
        self.reset_model()
        self.update_all()

    def tick(self):
        if not self.running:
            return

        dt = self.speed.get() * TICK_MS / 1000.0
        remaining = dt

        while self.t + remaining >= self.t_next:
            self.dur[self.i] += (
                self.t_next - self.t
            )  # время до момента перехода
            remaining -= self.t_next - self.t
            self.t = self.t_next
            self.i = self.j_next  # совершаем переход
            self.steps += 1
            self.traj.append((self.t, self.i))
            tau, self.j_next = next_event(self.i)
            self.t_next = self.t + tau

        self.dur[self.i] += remaining
        self.t += remaining

        self.update_status()
        self.tick_counter += 1
        if self.tick_counter % REDRAW_EVERY == 0:
            self.update_plots()
            self.update_table()

        self.after_id = self.root.after(TICK_MS, self.tick)

    def empirical(self):
        total = sum(self.dur)
        if total <= 0:
            return [0.0] * N
        return [d / total for d in self.dur]

    def update_all(self):
        self.update_status()
        self.update_plots()
        self.update_table()

    def update_status(self):
        self.status.config(
            text="День %.2f          ПОГОДА: %s"
            % (self.t, STATE_NAMES[self.i].upper()),
            bg=STATE_COLORS[self.i],
        )
        self.lbl_time.config(text="Модельное время: %.2f дн." % self.t)
        self.lbl_steps.config(text="Смен состояния: %d" % self.steps)

    def update_plots(self):
        window = 30.0

        self.ax_tr.clear()
        times = [p[0] for p in self.traj] + [self.t]
        states = [p[1] + 1 for p in self.traj] + [self.i + 1]
        self.ax_tr.step(
            times, states, where="post", linewidth=2, color="#1E88E5"
        )
        left = max(0.0, self.t - window)
        self.ax_tr.set_xlim(left, left + window)
        self.ax_tr.set_ylim(0.5, N + 0.5)
        self.ax_tr.set_yticks(range(1, N + 1))
        self.ax_tr.set_yticklabels(
            ["%d - %s" % (k + 1, STATE_NAMES[k]) for k in range(N)]
        )
        self.ax_tr.set_xlabel("время, дни")
        self.ax_tr.set_title("Траектория процесса (окно 30 дней)")
        self.ax_tr.grid(True, alpha=0.3)

        self.ax_bar.clear()
        emp = self.empirical()
        x = np.arange(N)
        self.ax_bar.bar(
            x - 0.2, emp, 0.4, label="эмпирическое", color="#42A5F5"
        )
        self.ax_bar.bar(
            x + 0.2, self.theory, 0.4, label="теоретическое", color="#EF5350"
        )
        for k in range(N):
            self.ax_bar.text(
                k - 0.2,
                emp[k] + 0.012,
                "%.3f" % emp[k],
                ha="center",
                fontsize=8,
            )
        self.ax_bar.set_xticks(x)
        self.ax_bar.set_xticklabels(
            ["%d - %s" % (k + 1, STATE_NAMES[k]) for k in range(N)]
        )
        self.ax_bar.set_ylim(0, 0.8)
        self.ax_bar.set_ylabel("вероятность")
        self.ax_bar.set_title(
            "Эмпирическое и теоретическое стационарное распределение"
        )
        self.ax_bar.legend(fontsize=8, loc="upper center", ncol=2)
        self.ax_bar.grid(True, axis="y", alpha=0.3)

        self.canvas.draw()

    def update_table(self):
        emp = self.empirical()
        for i in range(N):
            self.table.item(
                str(i),
                values=(
                    "%d - %s" % (i + 1, STATE_NAMES[i]),
                    "%.3f" % self.dur[i],
                    "%.4f" % emp[i],
                    "%.4f" % self.theory[i],
                    "%.4f" % abs(emp[i] - self.theory[i]),
                ),
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
