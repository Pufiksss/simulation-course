import math
import random
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

LAMBDA = 2.0
T = 10.0
N = 10000


def base_random():
    a = random.random()
    while a <= 0.0:
        a = random.random()
    return a


def next_interval(lam):
    alpha = base_random()
    return -math.log(alpha) / lam


def simulate_flow(lam, interval):
    moments = []
    t = 0.0
    while True:
        t = t + next_interval(lam)
        if t > interval:
            break
        moments.append(t)
    return moments


def count_events(lam, interval):
    count = 0
    t = 0.0
    while True:
        t = t + next_interval(lam)
        if t > interval:
            break
        count = count + 1
    return count


def run_experiment(lam, interval, runs):
    counts = []
    k = 0
    while k < runs:
        counts.append(count_events(lam, interval))
        k = k + 1
    return counts


def sample_mean(values):
    return sum(values) / len(values)


def sample_variance(values):
    m = sample_mean(values)
    return sum((v - m) ** 2 for v in values) / len(values)


def empirical_distribution(counts):
    top = max(counts)
    freq = [0] * (top + 1)
    for c in counts:
        freq[c] = freq[c] + 1
    return [f / len(counts) for f in freq]


def poisson_probs(a, top):
    probs = [math.exp(-a)]
    for m in range(1, top + 1):
        probs.append(probs[m - 1] * a / m)
    return probs


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная 8 - пуассоновский поток заявок на сервер")
        root.geometry("1150x800")

        self.counts = []
        self.moments = []

        self.build_interface()
        self.run()

    # -----------------------------------------------------------------

    def build_interface(self):
        box = ttk.LabelFrame(
            self.root,
            text="Характеристики числа заявок за интервал T",
            padding=6,
        )
        box.pack(side="bottom", fill="x", padx=8, pady=8)

        cols = ("name", "emp", "theory", "err")
        titles = {
            "name": "Характеристика",
            "emp": "Эмпирическое значение",
            "theory": "Теоретическое значение",
            "err": "Ошибка",
        }
        self.table = ttk.Treeview(box, columns=cols, show="headings", height=3)
        for c in cols:
            self.table.heading(c, text=titles[c])
            self.table.column(c, anchor="center", width=240)
        self.table.pack(fill="x")
        for i in range(3):
            self.table.insert("", "end", iid=str(i), values=("", "", "", ""))

        middle = ttk.Frame(self.root)
        middle.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        # ---------- панель управления ----------
        panel = ttk.LabelFrame(
            middle, text="Параметры моделирования", padding=10
        )
        panel.pack(side="left", fill="y", padx=(0, 8))

        self.entries = {}
        fields = [
            ("lam", "Интенсивность λ, заявок/сек:", str(LAMBDA)),
            ("T", "Длина интервала T, сек:", str(T)),
            ("N", "Число прогонов N:", str(N)),
        ]
        for key, text, value in fields:
            ttk.Label(panel, text=text).pack(anchor="w")
            e = ttk.Entry(panel, width=20, justify="center")
            e.insert(0, value)
            e.pack(anchor="w", pady=(0, 8))
            self.entries[key] = e

        ttk.Button(panel, text="Смоделировать", command=self.run).pack(
            fill="x", pady=(6, 2)
        )
        ttk.Button(
            panel, text="Новая реализация потока", command=self.new_realization
        ).pack(fill="x", pady=2)

        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=10)

        self.info = tk.Label(
            panel, justify="left", anchor="w", font=("Consolas", 9)
        )
        self.info.pack(anchor="w", fill="x")

        # ---------- графики ----------
        self.fig = plt.Figure(figsize=(8, 5.2), dpi=95)
        self.ax_flow = self.fig.add_subplot(2, 1, 1)
        self.ax_dist = self.fig.add_subplot(2, 1, 2)
        self.fig.subplots_adjust(
            left=0.10, right=0.97, top=0.92, bottom=0.11, hspace=0.55
        )
        self.canvas = FigureCanvasTkAgg(self.fig, master=middle)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

    def read_params(self):
        try:
            lam = float(self.entries["lam"].get().replace(",", "."))
            interval = float(self.entries["T"].get().replace(",", "."))
            runs = int(self.entries["N"].get())
        except ValueError:
            messagebox.showerror("Ошибка", "Параметры должны быть числами")
            return None
        if lam <= 0 or interval <= 0 or runs < 10:
            messagebox.showerror(
                "Ошибка", "Нужно: λ > 0, T > 0, N не меньше 10"
            )
            return None
        return lam, interval, runs

    def run(self):
        """Полный эксперимент: N прогонов, статобработка, отрисовка."""
        params = self.read_params()
        if params is None:
            return
        self.lam, self.interval, self.runs = params

        self.info.config(text="Идёт моделирование...")
        self.root.update()

        self.counts = run_experiment(self.lam, self.interval, self.runs)
        self.moments = simulate_flow(self.lam, self.interval)

        self.draw_flow()
        self.draw_distribution()
        self.fill_table()
        self.canvas.draw()

    def new_realization(self):
        """Показать другую единичную реализацию потока (верхний график)."""
        if not self.counts:
            return
        self.moments = simulate_flow(self.lam, self.interval)
        self.draw_flow()
        self.canvas.draw()

    def draw_flow(self):
        self.ax_flow.clear()
        for t in self.moments:
            self.ax_flow.plot([t, t], [0, 1], color="#1E88E5", linewidth=1.5)
        self.ax_flow.axhline(0, color="black", linewidth=1)
        self.ax_flow.set_xlim(0, self.interval)
        self.ax_flow.set_ylim(-0.2, 1.6)
        self.ax_flow.set_yticks([])
        self.ax_flow.set_xlabel("время, сек")
        self.ax_flow.set_title(
            "Одна реализация потока за T = %g сек, заявок: %d"
            % (self.interval, len(self.moments))
        )

    def draw_distribution(self):
        emp = empirical_distribution(self.counts)
        a = self.lam * self.interval
        theory = poisson_probs(a, len(emp) - 1)

        self.ax_dist.clear()
        x = list(range(len(emp)))
        self.ax_dist.bar(
            x, emp, width=0.7, color="#42A5F5", label="эмпирическое"
        )
        self.ax_dist.plot(
            x,
            theory,
            "o-",
            color="#EF5350",
            markersize=4,
            label="теоретическое (Пуассон)",
        )
        self.ax_dist.set_xlabel("число заявок за интервал T")
        self.ax_dist.set_ylabel("вероятность")
        self.ax_dist.set_title(
            "Распределение числа заявок, N = %d прогонов" % self.runs
        )
        self.ax_dist.legend(fontsize=8)
        self.ax_dist.grid(True, axis="y", alpha=0.3)

    def fill_table(self):
        a = self.lam * self.interval
        mean = sample_mean(self.counts)
        var = sample_variance(self.counts)

        rows = [
            ("Среднее число заявок", mean, a),
            ("Дисперсия числа заявок", var, a),
            (
                "Отношение дисперсии к среднему",
                var / mean if mean > 0 else 0,
                1.0,
            ),
        ]
        for i, (name, emp, theory) in enumerate(rows):
            self.table.item(
                str(i),
                values=(
                    name,
                    "%.4f" % emp,
                    "%.4f" % theory,
                    "%.4f" % abs(emp - theory),
                ),
            )

        self.info.config(
            text=(
                "λ·T = %.2f\n"
                "Прогонов: %d\n"
                "Минимум заявок: %d\n"
                "Максимум заявок: %d\n"
                "Всего заявок: %d"
                % (
                    a,
                    self.runs,
                    min(self.counts),
                    max(self.counts),
                    sum(self.counts),
                )
            )
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
