import math
import random
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ряд распределения по умолчанию (можно изменить в интерфейсе)
DEFAULT_VALUES = [1, 2, 3, 4, 5]
DEFAULT_PROBS = [0.1, 0.2, 0.4, 0.2, 0.1]
ROWS = len(DEFAULT_VALUES)

NORMAL_A = 5.0  # математическое ожидание
NORMAL_SIGMA = 2.0  # среднеквадратическое отклонение

SAMPLE_SIZES = [10, 100, 1000, 10000]

# критические значения хи-квадрат при уровне значимости 0.05
CHI2_CRITICAL = {
    1: 3.841,
    2: 5.991,
    3: 7.815,
    4: 9.488,
    5: 11.070,
    6: 12.592,
    7: 14.067,
    8: 15.507,
    9: 16.919,
    10: 18.307,
    11: 19.675,
    12: 21.026,
    13: 22.362,
    14: 23.685,
    15: 24.996,
    16: 26.296,
    17: 27.587,
    18: 28.869,
    19: 30.144,
    20: 31.410,
}


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


def normal_sum12(a, sigma):
    total = 0.0
    for _ in range(12):
        total += base_random()
    xi = total - 6.0
    return a + sigma * xi


def sample_mean(values):
    return sum(values) / len(values)


def sample_variance(values):
    m = sample_mean(values)
    return sum(v * v for v in values) / len(values) - m * m


def relative_error(empirical, theoretical):
    if theoretical == 0:
        return 0.0
    return abs(empirical - theoretical) / abs(theoretical) * 100.0


def chi2_critical(df):
    return CHI2_CRITICAL.get(df, 31.410)


def theory_mean_discrete(values, probs):
    return sum(values[i] * probs[i] for i in range(len(values)))


def theory_variance_discrete(values, probs):
    m = theory_mean_discrete(values, probs)
    return sum(values[i] ** 2 * probs[i] for i in range(len(values))) - m * m


def chi2_discrete(counts, probs, size):
    stat = 0.0
    used = 0
    for i in range(len(probs)):
        if probs[i] <= 0.0:
            continue
        expected = size * probs[i]
        stat += (counts[i] - expected) ** 2 / expected
        used += 1
    return stat, used - 1


def normal_cdf(x, a, sigma):
    return 0.5 * (1.0 + math.erf((x - a) / (sigma * math.sqrt(2.0))))


def sturges(size):
    return int(math.ceil(math.log(size, 2))) + 1


def build_bins(values, k, a, sigma):
    low = a - 4.0 * sigma
    width = 8.0 * sigma / k
    edges = [low + i * width for i in range(k + 1)]

    counts = [0] * k
    for v in values:
        index = int((v - low) / width)
        if index < 0:
            index = 0
        if index >= k:
            index = k - 1
        counts[index] += 1
    return edges, counts


def merge_small_bins(probs, counts, size, minimum=5.0):
    p = list(probs)
    c = list(counts)
    while len(p) > 2 and size * p[0] < minimum:
        p[1] += p[0]
        c[1] += c[0]
        p.pop(0)
        c.pop(0)
    while len(p) > 2 and size * p[-1] < minimum:
        p[-2] += p[-1]
        c[-2] += c[-1]
        p.pop()
        c.pop()
    return p, c


def chi2_continuous(edges, counts, size, a, sigma):
    k = len(counts)
    probs = []
    for i in range(k):
        left = 0.0 if i == 0 else normal_cdf(edges[i], a, sigma)
        right = 1.0 if i == k - 1 else normal_cdf(edges[i + 1], a, sigma)
        probs.append(right - left)

    probs, counts = merge_small_bins(probs, counts, size)

    stat = 0.0
    for i in range(len(counts)):
        expected = size * probs[i]
        stat += (counts[i] - expected) ** 2 / expected
    return stat, len(counts) - 1, len(counts)


def normal_density(x, a, sigma):
    return (
        1.0
        / (sigma * math.sqrt(2.0 * math.pi))
        * math.exp(-((x - a) ** 2) / (2.0 * sigma * sigma))
    )


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная 6 - моделирование случайных величин")
        root.geometry("1280x850")

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_discrete = ttk.Frame(notebook)
        self.tab_normal = ttk.Frame(notebook)
        notebook.add(
            self.tab_discrete, text="  Дискретная случайная величина  "
        )
        notebook.add(self.tab_normal, text="  Нормальная случайная величина  ")

        self.build_discrete_tab()
        self.build_normal_tab()

        self.run_discrete()
        self.run_normal()

    def build_discrete_tab(self):
        tab = self.tab_discrete

        box = ttk.LabelFrame(
            tab, text="Результаты по объёмам выборки", padding=6
        )
        box.pack(side="bottom", fill="x", pady=(6, 0))
        self.table_d = self.make_result_table(box)

        top = ttk.Frame(tab)
        top.pack(fill="both", expand=True)

        panel = ttk.LabelFrame(top, text="Ряд распределения", padding=8)
        panel.pack(side="left", fill="y", padx=(0, 8))

        ttk.Label(panel, text="Значение", width=10, anchor="center").grid(
            row=0, column=0, padx=2
        )
        ttk.Label(panel, text="Вероятность", width=12, anchor="center").grid(
            row=0, column=1, padx=2
        )

        self.value_entries = []
        self.prob_entries = []
        for i in range(ROWS):
            e_val = ttk.Entry(panel, width=10, justify="center")
            e_val.insert(0, str(DEFAULT_VALUES[i]))
            e_val.grid(row=i + 1, column=0, pady=1, padx=2)
            self.value_entries.append(e_val)

            e_prob = ttk.Entry(panel, width=12, justify="center")
            e_prob.insert(0, "%.2f" % DEFAULT_PROBS[i])
            e_prob.grid(row=i + 1, column=1, pady=1, padx=2)
            self.prob_entries.append(e_prob)

        row = ROWS + 1
        self.sum_label = ttk.Label(panel, text="", foreground="#555")
        self.sum_label.grid(row=row, column=0, columnspan=2, pady=(6, 0))

        ttk.Separator(panel, orient="horizontal").grid(
            row=row + 1, column=0, columnspan=2, sticky="ew", pady=8
        )
        ttk.Label(
            panel, text="Теоретические значения:", font=("Arial", 9, "bold")
        ).grid(row=row + 2, column=0, columnspan=2, sticky="w")
        self.theory_m_label = ttk.Label(panel, text="")
        self.theory_m_label.grid(
            row=row + 3, column=0, columnspan=2, sticky="w"
        )
        self.theory_d_label = ttk.Label(panel, text="")
        self.theory_d_label.grid(
            row=row + 4, column=0, columnspan=2, sticky="w"
        )

        ttk.Button(panel, text="Смоделировать", command=self.run_discrete).grid(
            row=row + 5, column=0, columnspan=2, sticky="ew", pady=(12, 2)
        )
        ttk.Button(
            panel, text="Вернуть исходный ряд", command=self.reset_distribution
        ).grid(row=row + 6, column=0, columnspan=2, sticky="ew")

        self.fig_d = plt.Figure(figsize=(9, 5.4), dpi=95)
        self.axes_d = [self.fig_d.add_subplot(2, 2, i + 1) for i in range(4)]
        self.fig_d.subplots_adjust(
            left=0.08,
            right=0.95,
            top=0.93,
            bottom=0.12,
            hspace=0.55,
            wspace=0.25,
        )
        self.canvas_d = FigureCanvasTkAgg(self.fig_d, master=top)
        self.canvas_d.get_tk_widget().pack(
            side="left", fill="both", expand=True
        )

    def read_distribution(self):
        values = []
        probs = []
        for i in range(ROWS):
            text_v = self.value_entries[i].get().replace(",", ".").strip()
            text_p = self.prob_entries[i].get().replace(",", ".").strip()
            try:
                values.append(float(text_v))
            except ValueError:
                messagebox.showerror(
                    "Ошибка ввода",
                    "Строка %d: значение «%s» не число." % (i + 1, text_v),
                )
                return None
            try:
                probs.append(float(text_p))
            except ValueError:
                messagebox.showerror(
                    "Ошибка ввода",
                    "Строка %d: вероятность «%s» не число." % (i + 1, text_p),
                )
                return None

        for i in range(ROWS):
            if probs[i] < 0:
                messagebox.showerror(
                    "Недопустимая вероятность",
                    "Строка %d: вероятность %g отрицательная.\n\n"
                    "Вероятность не может быть меньше нуля."
                    % (i + 1, probs[i]),
                )
                return None

        total = sum(probs)
        if abs(total - 1.0) > 1e-6:
            messagebox.showerror(
                "Сумма вероятностей",
                "Сумма вероятностей равна %.4f, а должна быть равна 1.\n\n"
                "Ряд распределения задаёт полную группу событий:\n"
                "величина обязана принять одно из перечисленных значений."
                % total,
            )
            return None

        if len(set(values)) < ROWS:
            messagebox.showerror(
                "Повторяющиеся значения",
                "В столбце значений есть одинаковые числа.\n\n"
                "Каждое значение должно встречаться один раз,\n"
                "иначе его вероятность задана дважды.",
            )
            return None

        return values, probs

    def reset_distribution(self):
        for i in range(ROWS):
            self.value_entries[i].delete(0, "end")
            self.value_entries[i].insert(0, str(DEFAULT_VALUES[i]))
            self.prob_entries[i].delete(0, "end")
            self.prob_entries[i].insert(0, "%.2f" % DEFAULT_PROBS[i])
        self.run_discrete()

    def run_discrete(self):
        distribution = self.read_distribution()
        if distribution is None:
            return
        x_values, x_probs = distribution

        theory_m = theory_mean_discrete(x_values, x_probs)
        theory_d = theory_variance_discrete(x_values, x_probs)

        self.sum_label.config(text="сумма вероятностей: %.4f" % sum(x_probs))
        self.theory_m_label.config(text="M[X] = %.4f" % theory_m)
        self.theory_d_label.config(text="D[X] = %.4f" % theory_d)

        top_prob = max(x_probs)

        for position, size in enumerate(SAMPLE_SIZES):
            counts = [0] * ROWS
            values = []
            for _ in range(size):
                index = generate_dsv(x_probs)
                counts[index] += 1
                values.append(x_values[index])

            empirical = [c / size for c in counts]
            mean = sample_mean(values)
            variance = sample_variance(values)
            stat, df = chi2_discrete(counts, x_probs, size)

            if df < 1:
                chi_text = "-"
                crit_text = "-"
                verdict = "критерий неприменим"
            else:
                critical = chi2_critical(df)
                chi_text = "%.3f" % stat
                crit_text = "%.3f (df = %d)" % (critical, df)
                verdict = "принимается" if stat < critical else "ОТВЕРГАЕТСЯ"

            var_err = (
                "-"
                if theory_d == 0
                else "%.2f %%" % relative_error(variance, theory_d)
            )

            self.table_d.item(
                str(position),
                values=(
                    size,
                    "%.4f" % mean,
                    "%.2f %%" % relative_error(mean, theory_m),
                    "%.4f" % variance,
                    var_err,
                    chi_text,
                    crit_text,
                    verdict,
                ),
            )

            ax = self.axes_d[position]
            ax.clear()
            ax.plot(
                x_values, empirical, "o-", color="#1E88E5", label="эмпирические"
            )
            ax.plot(
                x_values, x_probs, "s--", color="#EF5350", label="теоретические"
            )
            ax.set_xticks(x_values)
            ax.set_ylim(0, min(1.0, top_prob * 1.8 + 0.1))
            ax.set_title("N = %d" % size, fontsize=10)
            ax.set_xlabel("значение", fontsize=8)
            ax.set_ylabel("вероятность", fontsize=8)
            ax.legend(fontsize=7, loc="upper center", ncol=2)
            ax.grid(True, alpha=0.3)

        self.canvas_d.draw()

    def build_normal_tab(self):
        tab = self.tab_normal

        box = ttk.LabelFrame(
            tab, text="Результаты по объёмам выборки", padding=6
        )
        box.pack(side="bottom", fill="x", pady=(6, 0))
        self.table_n = self.make_result_table(box)

        top = ttk.Frame(tab)
        top.pack(fill="both", expand=True)

        panel = ttk.LabelFrame(top, text="Параметры и метод", padding=8)
        panel.pack(side="left", fill="y", padx=(0, 8))

        ttk.Label(panel, text="Математическое ожидание a:").pack(anchor="w")
        self.entry_a = ttk.Entry(panel, width=16, justify="center")
        self.entry_a.insert(0, str(NORMAL_A))
        self.entry_a.pack(anchor="w", pady=(0, 8))

        ttk.Label(panel, text="Стандартное отклонение σ:").pack(anchor="w")
        self.entry_sigma = ttk.Entry(panel, width=16, justify="center")
        self.entry_sigma.insert(0, str(NORMAL_SIGMA))
        self.entry_sigma.pack(anchor="w", pady=(0, 12))

        ttk.Button(panel, text="Смоделировать", command=self.run_normal).pack(
            fill="x", pady=(14, 0)
        )

        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=10)
        self.info_n = tk.Label(
            panel, justify="left", anchor="w", font=("Consolas", 9)
        )
        self.info_n.pack(anchor="w", fill="x")

        self.fig_n = plt.Figure(figsize=(9, 5.4), dpi=95)
        self.axes_n = [self.fig_n.add_subplot(2, 2, i + 1) for i in range(4)]
        self.fig_n.subplots_adjust(
            left=0.08,
            right=0.95,
            top=0.93,
            bottom=0.12,
            hspace=0.55,
            wspace=0.25,
        )
        self.canvas_n = FigureCanvasTkAgg(self.fig_n, master=top)
        self.canvas_n.get_tk_widget().pack(
            side="left", fill="both", expand=True
        )

    def run_normal(self):
        try:
            a = float(self.entry_a.get().replace(",", "."))
            sigma = abs(float(self.entry_sigma.get().replace(",", ".")))
        except ValueError:
            messagebox.showerror(
                "Ошибка ввода",
                "Параметры a и σ должны быть числами.\n"
                "Разделитель дробной части - точка или запятая.",
            )
            return
        if sigma <= 0:
            messagebox.showerror(
                "Недопустимое σ",
                "σ должно быть строго больше нуля.\n\n"
                "σ - это среднеквадратическое отклонение, мера разброса\n"
                "значений вокруг среднего. При σ = 0 случайности нет:\n"
                "все значения совпали бы с a.",
            )
            return

        generator = normal_sum12
        theory_d = sigma * sigma
        note = []

        for position, size in enumerate(SAMPLE_SIZES):
            values = [generator(a, sigma) for _ in range(size)]

            mean = sample_mean(values)
            variance = sample_variance(values)

            k = sturges(size)
            edges, counts = build_bins(values, k, a, sigma)
            stat, df, used = chi2_continuous(edges, counts, size, a, sigma)
            critical = chi2_critical(df)
            if used < k:
                note.append("N = %d: %d -> %d" % (size, k, used))

            self.table_n.item(
                str(position),
                values=(
                    size,
                    "%.4f" % mean,
                    "%.2f %%" % relative_error(mean, a),
                    "%.4f" % variance,
                    "%.2f %%" % relative_error(variance, theory_d),
                    "%.3f" % stat,
                    "%.3f (df = %d)" % (critical, df),
                    "принимается" if stat < critical else "ОТВЕРГАЕТСЯ",
                ),
            )

            ax = self.axes_n[position]
            ax.clear()
            width = edges[1] - edges[0]
            centers = [(edges[i] + edges[i + 1]) / 2 for i in range(k)]
            heights = [c / (size * width) for c in counts]
            ax.bar(
                centers,
                heights,
                width=width * 0.9,
                color="#42A5F5",
                label="гистограмма",
            )

            left = a - 4 * sigma
            xs = [left + 8 * sigma * i / 150 for i in range(151)]
            ys = [normal_density(x, a, sigma) for x in xs]
            ax.plot(xs, ys, color="#EF5350", linewidth=2, label="теория")

            ax.set_title("N = %d, интервалов %d" % (size, k), fontsize=10)
            ax.set_xlabel("значение", fontsize=8)
            ax.set_ylabel("плотность", fontsize=8)
            ax.legend(fontsize=7, loc="upper right")
            ax.grid(True, axis="y", alpha=0.3)

        self.canvas_n.draw()

        text = (
            "Число интервалов выбрано\n"
            "по формуле Стёрджеса:\n"
            "  k = ceil(log2(N)) + 1\n\n"
            "Для критерия хи-квадрат\n"
            "интервалы с ожидаемым\n"
            "числом меньше 5\n"
            "объединены с соседними:\n"
        )
        for line in note:
            text += "  " + line + "\n"
        self.info_n.config(text=text)

    def make_result_table(self, parent):
        cols = (
            "n",
            "mean",
            "mean_err",
            "var",
            "var_err",
            "chi",
            "crit",
            "verdict",
        )
        titles = {
            "n": "N",
            "mean": "Среднее",
            "mean_err": "Погрешность среднего",
            "var": "Дисперсия",
            "var_err": "Погрешность дисперсии",
            "chi": "Статистика χ²",
            "crit": "Критическое χ²",
            "verdict": "Гипотеза",
        }
        widths = {
            "n": 80,
            "mean": 130,
            "mean_err": 170,
            "var": 130,
            "var_err": 170,
            "chi": 130,
            "crit": 130,
            "verdict": 160,
        }

        table = ttk.Treeview(parent, columns=cols, show="headings", height=4)
        for c in cols:
            table.heading(c, text=titles[c])
            table.column(c, anchor="center", width=widths[c])
        table.pack(fill="x")
        for i in range(4):
            table.insert("", "end", iid=str(i), values=("",) * 8)
        return table


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
