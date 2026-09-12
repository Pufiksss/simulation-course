import math
import random
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

LAMBDA = 0.8  # интенсивность прихода клиентов, чел/мин
MU = 1.0  # интенсивность обслуживания, чел/мин
SIM_TIME = 100000  # длительность моделирования, мин
WARMUP = 1000  # прогрев (отбрасываем переходный режим), мин
LONG_WAIT = 10.0  # порог "долгого ожидания", мин

INF = float("inf")


def base_random():
    a = random.random()
    while a <= 0.0:
        a = random.random()
    return a


def exp_rv(rate):
    return -math.log(base_random()) / rate


def simulate(lam, mu, sim_time, warmup):
    t = 0.0
    x = 0  # клиент у оператора
    y = 0  # клиенты в очереди
    queue = []  # храним время прихода клиентов в очереди
    serving_arrival = None  # момент прихода того, кого обслуживают сейчас

    time_in_state = {}  # n клиентов в системе -> суммарное время
    waits = []  # сколько каждый простоял в очереди
    systems = []

    while t < sim_time:
        tau = exp_rv(lam)  # время прихода следующего клиента
        if x > 0:
            delta = exp_rv(mu * x)  # окончание обслуживания
        else:
            delta = INF  # обслуживать некого

        collect = t >= warmup  # после прогрева копим статистику
        n = x + y  # клиентов в системе сейчас

        if tau < delta:
            if collect:
                time_in_state[n] = time_in_state.get(n, 0.0) + tau
            t = t + tau

            if x < 1:
                x = x + 1  # оператор свободен, сразу обслуживаем
                serving_arrival = t
                if collect:
                    waits.append(0.0)  # ждать не пришлось
            else:
                y = y + 1  # оператор занят, встаём в очередь
                queue.append(t)

        else:
            if collect:
                time_in_state[n] = time_in_state.get(n, 0.0) + delta
            t = t + delta

            if collect and serving_arrival is not None:
                systems.append(t - serving_arrival)

            if y == 0:
                x = x - 1  # очередь пуста, оператор освободился
                serving_arrival = None
            else:
                y = y - 1  # берём на обслуживание первого из очереди
                arrived = queue.pop(0)
                if collect:
                    waits.append(t - arrived)
                serving_arrival = arrived

    return time_in_state, waits, systems, sim_time - warmup


def state_distribution(time_in_state, total_time):
    top = max(time_in_state.keys())
    return [time_in_state.get(n, 0.0) / total_time for n in range(top + 1)]


def mean(values):
    return sum(values) / len(values)


def histogram(values, bins, top):
    width = top / bins
    counts = [0] * bins
    for v in values:
        k = int(v / width)
        if k >= bins:
            k = bins - 1
        counts[k] = counts[k] + 1
    centers = [(i + 0.5) * width for i in range(bins)]
    heights = [c / (len(values) * width) for c in counts]
    return centers, heights, width


# сколько за границей
def share_above(values, threshold):
    return sum(1 for v in values if v > threshold) / len(values)


def theory(lam, mu, threshold):
    rho = lam / mu
    return {
        "rho": rho,
        "L": rho / (1 - rho),  #  среднее число клиентов в системе
        "Lq": rho * rho / (1 - rho),  # средняя длина очереди
        "Wq": rho / (mu - lam),  # среднее время ожидания
        "W": 1.0 / (mu - lam),  # среднее время в системе
        "P_long": rho * math.exp(-(mu - lam) * threshold),
    }


def theory_state_probs(rho, top):
    return [(1 - rho) * rho**n for n in range(top + 1)]


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная 9 - пункт выдачи заказов, модель M/M/1")
        root.geometry("1200x820")

        self.build_interface()
        self.run()

    def build_interface(self):
        box = ttk.LabelFrame(
            self.root, text="Параметры функционирования системы", padding=6
        )
        box.pack(side="bottom", fill="x", padx=8, pady=8)

        cols = ("name", "emp", "theory", "err")
        titles = {
            "name": "Показатель",
            "emp": "Эмпирическое значение",
            "theory": "Теоретическое значение",
            "err": "Ошибка",
        }
        self.table = ttk.Treeview(box, columns=cols, show="headings", height=6)
        for c in cols:
            self.table.heading(c, text=titles[c])
            self.table.column(c, anchor="center", width=250)
        self.table.pack(fill="x")
        for i in range(6):
            self.table.insert("", "end", iid=str(i), values=("", "", "", ""))

        middle = ttk.Frame(self.root)
        middle.pack(fill="both", expand=True, padx=8, pady=(8, 0))

        panel = ttk.LabelFrame(middle, text="Параметры модели", padding=10)
        panel.pack(side="left", fill="y", padx=(0, 8))

        self.entries = {}
        fields = [
            ("lam", "Приход клиентов λ, чел/мин:", str(LAMBDA)),
            ("mu", "Обслуживание μ, чел/мин:", str(MU)),
            ("time", "Время моделирования, мин:", str(SIM_TIME)),
            ("warmup", "Прогрев, мин:", str(WARMUP)),
            ("long", "Порог долгого ожидания, мин:", str(LONG_WAIT)),
        ]
        for key, text, value in fields:
            ttk.Label(panel, text=text).pack(anchor="w")
            e = ttk.Entry(panel, width=22, justify="center")
            e.insert(0, value)
            e.pack(anchor="w", pady=(0, 7))
            self.entries[key] = e

        ttk.Button(panel, text="Смоделировать", command=self.run).pack(
            fill="x", pady=(6, 2)
        )

        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=10)

        self.info = tk.Label(
            panel, justify="left", anchor="w", font=("Consolas", 9)
        )
        self.info.pack(anchor="w", fill="x")

        self.fig = plt.Figure(figsize=(8, 5.2), dpi=95)
        self.ax_state = self.fig.add_subplot(2, 1, 1)
        self.ax_wait = self.fig.add_subplot(2, 1, 2)
        self.fig.subplots_adjust(
            left=0.11, right=0.97, top=0.92, bottom=0.11, hspace=0.55
        )
        self.canvas = FigureCanvasTkAgg(self.fig, master=middle)
        self.canvas.get_tk_widget().pack(side="left", fill="both", expand=True)

    def read_params(self):
        try:
            lam = float(self.entries["lam"].get().replace(",", "."))
            mu = float(self.entries["mu"].get().replace(",", "."))
            sim_time = float(self.entries["time"].get().replace(",", "."))
            warmup = float(self.entries["warmup"].get().replace(",", "."))
            threshold = float(self.entries["long"].get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка", "Параметры должны быть числами")
            return None

        if lam <= 0 or mu <= 0 or sim_time <= warmup or threshold <= 0:
            messagebox.showerror(
                "Ошибка",
                "Нужно: λ > 0, μ > 0, порог > 0,\n"
                "время моделирования больше прогрева",
            )
            return None

        if lam >= mu:
            messagebox.showerror(
                "Система перегружена",
                "Загрузка ρ = λ/μ = %.2f, а должно быть меньше 1.\n\n"
                "Клиенты приходят быстрее, чем оператор успевает их\n"
                "обслуживать, очередь растёт неограниченно и\n"
                "стационарного режима не существует." % (lam / mu),
            )
            return None

        return lam, mu, sim_time, warmup, threshold

    def run(self):
        params = self.read_params()
        if params is None:
            return
        self.lam, self.mu, sim_time, warmup, self.threshold = params

        self.info.config(text="Идёт моделирование...")
        self.root.update()

        time_in_state, waits, systems, total = simulate(
            self.lam, self.mu, sim_time, warmup
        )

        self.state_probs = state_distribution(time_in_state, total)
        self.waits = waits
        self.systems = systems
        self.th = theory(self.lam, self.mu, self.threshold)

        self.draw_states()
        self.draw_waits()
        self.fill_table()
        self.canvas.draw()

    def draw_states(self):
        """Полигон частот: распределение числа клиентов в системе."""
        emp = self.state_probs
        top = max(n for n in range(len(emp)) if emp[n] > 0.0005)
        emp = emp[: top + 1]
        th = theory_state_probs(self.th["rho"], top)

        self.ax_state.clear()
        x = list(range(top + 1))
        self.ax_state.plot(
            x, emp, "o-", color="#1E88E5", markersize=5, label="эмпирическое"
        )
        self.ax_state.plot(
            x,
            th,
            "s--",
            color="#EF5350",
            markersize=4,
            label="теоретическое M/M/1",
        )
        self.ax_state.set_xlabel("число клиентов в системе")
        self.ax_state.set_ylabel("вероятность")
        self.ax_state.set_title(
            "Полигон частот: распределение числа клиентов в системе"
        )
        self.ax_state.legend(fontsize=8)
        self.ax_state.grid(True, alpha=0.3)

    def draw_waits(self):
        """Гистограмма частот: время ожидания клиента в очереди."""
        top = 6.0 / (self.mu - self.lam)  # разумный правый край
        centers, heights, width = histogram(self.waits, 30, top)

        self.ax_wait.clear()
        self.ax_wait.bar(
            centers,
            heights,
            width=width * 0.9,
            color="#42A5F5",
            label="эмпирическая гистограмма",
        )

        rate = self.mu - self.lam
        xs = [top * i / 200 for i in range(201)]
        ys = [self.th["rho"] * rate * math.exp(-rate * w) for w in xs]
        self.ax_wait.plot(
            xs,
            ys,
            color="#EF5350",
            linewidth=2,
            label="теоретическая плотность",
        )

        self.ax_wait.axvline(
            self.threshold,
            color="green",
            linestyle="--",
            linewidth=1.5,
            label="порог долгого ожидания",
        )
        self.ax_wait.set_xlabel("время ожидания в очереди, мин")
        self.ax_wait.set_ylabel("плотность частоты")
        self.ax_wait.set_title(
            "Гистограмма частот: время ожидания клиента в очереди"
        )
        self.ax_wait.legend(fontsize=8)
        self.ax_wait.grid(True, axis="y", alpha=0.3)

    def fill_table(self):
        emp = self.state_probs

        rho_emp = 1.0 - emp[0]
        L_emp = sum(n * emp[n] for n in range(len(emp)))
        Lq_emp = sum(max(n - 1, 0) * emp[n] for n in range(len(emp)))
        Wq_emp = mean(self.waits)
        W_emp = mean(self.systems)
        p_long_emp = share_above(self.waits, self.threshold)

        rows = [
            ("Коэффициент загрузки оператора", rho_emp, self.th["rho"]),
            ("Среднее число клиентов в системе", L_emp, self.th["L"]),
            ("Средняя длина очереди", Lq_emp, self.th["Lq"]),
            ("Среднее время ожидания, мин", Wq_emp, self.th["Wq"]),
            ("Среднее время в системе, мин", W_emp, self.th["W"]),
            (
                "Вероятность ожидания > %g мин" % self.threshold,
                p_long_emp,
                self.th["P_long"],
            ),
        ]
        for i, (name, e, t) in enumerate(rows):
            self.table.item(
                str(i),
                values=(name, "%.4f" % e, "%.4f" % t, "%.4f" % abs(e - t)),
            )

        self.info.config(
            text=(
                "Обслужено клиентов: %d\n"
                "Максимум в системе: %d\n"
                "Максимальное ожидание: %.1f мин\n"
                "Ждали дольше %g мин: %.1f%%\n"
                "Более 5 клиентов в системе: %.2f%%"
                % (
                    len(self.systems),
                    len(emp) - 1,
                    max(self.waits),
                    self.threshold,
                    p_long_emp * 100,
                    sum(emp[n] for n in range(6, len(emp))) * 100,
                )
            )
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
