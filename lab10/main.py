import math
import random
import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

LAMBDA = 1.2  # приход клиентов, чел/мин
MU = 0.5  # обслуживание одним бариста, чел/мин (2 минуты на кофе)
SERVERS = 3  # число бариста
QUEUE_PLACES = 5  # мест в очереди
PATIENCE = 5.0  # среднее терпение клиента, мин
WARMUP = 200.0  # прогрев, мин

INF = float("inf")


def base_random():
    a = random.random()
    while a <= 0.0:
        a = random.random()
    return a


def exp_rv(rate):
    return -math.log(base_random()) / rate


class Agent:
    def __init__(self, cafe):
        self.cafe = cafe

    def get_next_event(self):
        return INF

    def process_event(self):
        pass


class Door(Agent):
    def __init__(self, cafe):
        Agent.__init__(self, cafe)
        self.next_arrival = exp_rv(cafe.lam)

    def get_next_event(self):
        return self.next_arrival

    def process_event(self):
        self.cafe.client_arrived()
        self.next_arrival = self.cafe.t + exp_rv(self.cafe.lam)


class Barista(Agent):
    def __init__(self, cafe, number):
        Agent.__init__(self, cafe)
        self.number = number
        self.client = None  # кого обслуживаем
        self.finish_time = INF  # когда закончим (INF, если свободен)

    def is_free(self):
        return self.client is None

    def start_service(self, client):
        self.client = client
        self.finish_time = self.cafe.t + exp_rv(self.cafe.mu)

    def get_next_event(self):
        return self.finish_time

    def process_event(self):
        self.cafe.served = self.cafe.served + 1
        self.client = None
        self.finish_time = INF
        client = self.cafe.take_from_queue()
        if client is not None:
            self.start_service(client)


class Client(Agent):
    def __init__(self, cafe, arrival_time):
        Agent.__init__(self, cafe)
        self.arrival_time = arrival_time
        self.patience_end = arrival_time + exp_rv(1.0 / cafe.patience)

    def get_next_event(self):
        return self.patience_end

    def process_event(self):
        self.cafe.client_gave_up(self)


class Cafe:
    def __init__(self, lam, mu, servers, places, patience, warmup):
        self.lam = lam
        self.mu = mu
        self.places = places
        self.patience = patience
        self.warmup = warmup

        self.t = 0.0
        self.door = Door(self)
        self.baristas = [Barista(self, i + 1) for i in range(servers)]
        self.queue = []

        # счётчики
        self.came = 0  # всего пришло
        self.served = 0  # обслужено
        self.refused = 0  # ушли, не найдя места
        self.gave_up = 0  # ушли, не дождавшись

        # статистика
        self.time_busy = {}  # число занятых бариста -> время
        self.time_queue = {}  # длина очереди -> время
        self.waits = []  # время пребывания в очереди по клиентам
        self.stat_time = 0.0  # сколько времени копится статистика

    def free_barista(self):
        for b in self.baristas:
            if b.is_free():
                return b
        return None

    def busy_count(self):
        return sum(1 for b in self.baristas if not b.is_free())

    def client_arrived(self):
        self.came = self.came + 1
        barista = self.free_barista()

        if barista is not None:
            # есть свободный бариста - обслуживаем сразу, ждать не пришлось
            barista.start_service(Client(self, self.t))
            self.record_wait(0.0)

        elif len(self.queue) < self.places:
            # ПРАВИЛО 1: место в очереди есть - встаём
            self.queue.append(Client(self, self.t))

        else:
            # ПРАВИЛО 1: мест нет - разворачиваемся и уходим (отказ)
            self.refused = self.refused + 1

    def take_from_queue(self):
        """Бариста освободился и забирает первого из очереди."""
        if not self.queue:
            return None
        client = self.queue.pop(0)
        self.record_wait(self.t - client.arrival_time)
        return client

    def client_gave_up(self, client):
        """ПРАВИЛО 2: клиент не дождался и ушёл из очереди."""
        self.queue.remove(client)
        self.gave_up = self.gave_up + 1
        self.record_wait(self.t - client.arrival_time)

    def record_wait(self, value):
        if self.t >= self.warmup:
            self.waits.append(value)

    def all_agents(self):
        return [self.door] + self.baristas + self.queue

    def step(self):
        best_time = INF
        best_agent = None
        for agent in self.all_agents():
            ti = agent.get_next_event()
            if ti < best_time:
                best_time = ti
                best_agent = agent

        self.accumulate(best_time - self.t)
        self.t = best_time
        best_agent.process_event()

    def accumulate(self, dt):
        if self.t < self.warmup:
            return
        busy = self.busy_count()
        qlen = len(self.queue)
        self.time_busy[busy] = self.time_busy.get(busy, 0.0) + dt
        self.time_queue[qlen] = self.time_queue.get(qlen, 0.0) + dt
        self.stat_time = self.stat_time + dt

    def run_until(self, until):
        """Прокрутить модель до заданного момента времени."""
        while self.t < until:
            self.step()

    def busy_distribution(self):
        """Эмпирическое распределение числа занятых бариста."""
        if self.stat_time <= 0:
            return [0.0] * (len(self.baristas) + 1)
        return [
            self.time_busy.get(k, 0.0) / self.stat_time
            for k in range(len(self.baristas) + 1)
        ]

    def queue_distribution(self):
        """Эмпирическое распределение длины очереди."""
        if self.stat_time <= 0:
            return [0.0] * (self.places + 1)
        return [
            self.time_queue.get(k, 0.0) / self.stat_time
            for k in range(self.places + 1)
        ]


def theory_probs(lam, mu, servers, places, patience):
    nu = 1.0 / patience
    top = servers + places
    p = [1.0]
    for n in range(1, top + 1):
        out_rate = min(n, servers) * mu + max(n - servers, 0) * nu
        p.append(p[n - 1] * lam / out_rate)
    total = sum(p)
    return [v / total for v in p]


def theory_summary(lam, mu, servers, places, patience):
    p = theory_probs(lam, mu, servers, places, patience)
    top = servers + places

    busy = [0.0] * (servers + 1)
    queue = [0.0] * (places + 1)
    for n in range(top + 1):
        busy[min(n, servers)] += p[n]
        queue[max(n - servers, 0)] += p[n]

    p_refuse = p[top]  # все места заняты
    Lq = sum(k * queue[k] for k in range(places + 1))  # средняя длина очереди
    lam_in = lam * (1 - p_refuse)  # реально вошедший поток
    Wq = Lq / lam_in if lam_in > 0 else 0.0  # формула Литтла

    return {
        "busy": busy,
        "queue": queue,
        "idle": busy[0],  # все бариста свободны
        "load": sum(k * busy[k] for k in range(servers + 1)) / servers,
        "Lq": Lq,
        "Wq": Wq,
        "p_refuse": p_refuse,
    }


TICK_MS = 50


class App:
    def __init__(self, root):
        self.root = root
        root.title("Лабораторная 10 - агентная модель кофейни")
        root.geometry("1280x870")

        self.running = False
        self.after_id = None
        self.frame_counter = 0

        self.build_interface()
        self.reset()

    def build_interface(self):
        box = ttk.LabelFrame(
            self.root, text="Параметры функционирования системы", padding=6
        )
        box.pack(side="bottom", fill="x", padx=8, pady=6)

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
            self.table.column(c, anchor="center", width=260)
        self.table.pack(fill="x")
        for i in range(6):
            self.table.insert("", "end", iid=str(i), values=("", "", "", ""))

        self.timer = tk.Label(
            self.root,
            text="",
            font=("Arial", 16, "bold"),
            bg="#ECEFF1",
            relief="ridge",
            bd=2,
            height=2,
        )
        self.timer.pack(fill="x", padx=8, pady=(8, 4))

        middle = ttk.Frame(self.root)
        middle.pack(fill="both", expand=True, padx=8)

        panel = ttk.LabelFrame(middle, text="Параметры и управление", padding=8)
        panel.pack(side="left", fill="y", padx=(0, 8))

        self.entries = {}
        fields = [
            ("lam", "Приход клиентов λ, чел/мин:", str(LAMBDA)),
            ("mu", "Обслуживание μ, чел/мин:", str(MU)),
            ("servers", "Число бариста N:", str(SERVERS)),
            ("places", "Мест в очереди:", str(QUEUE_PLACES)),
            ("patience", "Среднее терпение, мин:", str(PATIENCE)),
            ("warmup", "Прогрев, мин:", str(WARMUP)),
        ]
        for key, text, value in fields:
            ttk.Label(panel, text=text).pack(anchor="w")
            e = ttk.Entry(panel, width=20, justify="center")
            e.insert(0, value)
            e.pack(anchor="w", pady=(0, 5))
            self.entries[key] = e

        ttk.Label(panel, text="Скорость, минут в секунду:").pack(anchor="w")
        self.speed = tk.DoubleVar(value=10.0)
        ttk.Scale(
            panel,
            from_=1.0,
            to=2000.0,
            variable=self.speed,
            orient="horizontal",
            length=170,
            command=self.on_speed,
        ).pack(anchor="w")
        self.speed_label = ttk.Label(panel, text="10")
        self.speed_label.pack(anchor="w", pady=(0, 6))

        self.btn_start = ttk.Button(panel, text="Старт", command=self.start)
        self.btn_start.pack(fill="x", pady=1)
        self.btn_pause = ttk.Button(
            panel, text="Пауза", command=self.pause, state="disabled"
        )
        self.btn_pause.pack(fill="x", pady=1)
        ttk.Button(panel, text="Сброс", command=self.reset).pack(
            fill="x", pady=1
        )

        ttk.Separator(panel, orient="horizontal").pack(fill="x", pady=8)
        self.info = tk.Label(
            panel, justify="left", anchor="w", font=("Consolas", 9)
        )
        self.info.pack(anchor="w", fill="x")

        right = ttk.Frame(middle)
        right.pack(side="left", fill="both", expand=True)

        vis = ttk.LabelFrame(right, text="Кофейня", padding=4)
        vis.pack(fill="x")
        self.canvas_vis = tk.Canvas(
            vis, height=180, bg="white", highlightthickness=0
        )
        self.canvas_vis.pack(fill="x")

        self.fig = plt.Figure(figsize=(9, 3.3), dpi=95)
        self.ax_busy = self.fig.add_subplot(1, 3, 1)
        self.ax_queue = self.fig.add_subplot(1, 3, 2)
        self.ax_wait = self.fig.add_subplot(1, 3, 3)
        self.fig.subplots_adjust(
            left=0.07, right=0.98, top=0.86, bottom=0.20, wspace=0.35
        )
        self.canvas_fig = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas_fig.get_tk_widget().pack(
            fill="both", expand=True, pady=(6, 0)
        )

    def read_params(self):
        try:
            lam = float(self.entries["lam"].get().replace(",", "."))
            mu = float(self.entries["mu"].get().replace(",", "."))
            servers = int(self.entries["servers"].get())
            places = int(self.entries["places"].get())
            patience = float(self.entries["patience"].get().replace(",", "."))
            warmup = float(self.entries["warmup"].get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Ошибка", "Параметры должны быть числами")
            return None
        if lam <= 0 or mu <= 0 or servers < 1 or places < 0 or patience <= 0:
            messagebox.showerror(
                "Ошибка",
                "Нужно: λ > 0, μ > 0, бариста хотя бы один,\n"
                "мест не меньше нуля, терпение > 0",
            )
            return None
        return lam, mu, servers, places, patience, warmup

    def on_speed(self, _value):
        self.speed_label.config(text="%.0f" % self.speed.get())

    def reset(self):
        self.pause()
        params = self.read_params()
        if params is None:
            return
        lam, mu, servers, places, patience, warmup = params
        self.cafe = Cafe(lam, mu, servers, places, patience, warmup)
        self.th = theory_summary(lam, mu, servers, places, patience)
        self.redraw_all()

    def start(self):
        if self.running:
            return
        self.running = True
        self.btn_start.config(state="disabled")
        self.btn_pause.config(state="normal")
        self.tick()

    def pause(self):
        self.running = False
        if hasattr(self, "btn_start"):
            self.btn_start.config(state="normal")
            self.btn_pause.config(state="disabled")
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def tick(self):
        if not self.running:
            return

        dt = self.speed.get() * TICK_MS / 1000.0
        self.cafe.run_until(self.cafe.t + dt)

        self.draw_cafe()
        self.update_timer()
        self.frame_counter = self.frame_counter + 1
        if self.frame_counter % 6 == 0:
            self.draw_charts()
            self.fill_table()

        self.after_id = self.root.after(TICK_MS, self.tick)

    def redraw_all(self):
        self.draw_cafe()
        self.update_timer()
        self.draw_charts()
        self.fill_table()

    def update_timer(self):
        c = self.cafe
        hours = int(c.t // 60)
        minutes = c.t - hours * 60
        self.timer.config(
            text="Модельное время: %d ч %05.2f мин          "
            "Пришло: %d    Обслужено: %d    Отказ: %d    Не дождались: %d"
            % (hours, minutes, c.came, c.served, c.refused, c.gave_up)
        )

        self.info.config(
            text=(
                "Занято бариста: %d из %d\n"
                "В очереди: %d из %d\n"
                "Статистика за: %.0f мин\n"
                "Записей ожидания: %d"
                % (
                    c.busy_count(),
                    len(c.baristas),
                    len(c.queue),
                    c.places,
                    c.stat_time,
                    len(c.waits),
                )
            )
        )

    def draw_cafe(self):
        """Картинка кофейни: бариста и очередь."""
        cv = self.canvas_vis
        cv.delete("all")
        c = self.cafe

        cv.create_text(
            10, 12, text="Бариста", anchor="w", font=("Arial", 10, "bold")
        )
        for i, b in enumerate(c.baristas):
            x = 15 + i * 105
            color = "#A5D6A7" if b.is_free() else "#EF9A9A"
            cv.create_rectangle(x, 25, x + 90, 75, fill=color, outline="#555")
            cv.create_text(
                x + 45, 40, text="Бариста %d" % b.number, font=("Arial", 9)
            )
            cv.create_text(
                x + 45,
                60,
                text="свободен" if b.is_free() else "занят",
                font=("Arial", 9, "bold"),
            )

        cv.create_text(
            10, 100, text="Очередь", anchor="w", font=("Arial", 10, "bold")
        )
        for k in range(c.places):
            x = 15 + k * 60
            if k < len(c.queue):
                waited = c.t - c.queue[k].arrival_time
                cv.create_rectangle(
                    x, 115, x + 50, 165, fill="#90CAF9", outline="#555"
                )
                cv.create_text(x + 25, 132, text="клиент", font=("Arial", 8))
                cv.create_text(
                    x + 25,
                    150,
                    text="%.1f мин" % waited,
                    font=("Arial", 8, "bold"),
                )
            else:
                cv.create_rectangle(
                    x,
                    115,
                    x + 50,
                    165,
                    fill="#ECEFF1",
                    outline="#BBB",
                    dash=(3, 3),
                )
                cv.create_text(
                    x + 25, 140, text="свободно", fill="#999", font=("Arial", 8)
                )

    def draw_charts(self):
        c = self.cafe

        emp = c.busy_distribution()
        x = list(range(len(emp)))
        self.ax_busy.clear()
        self.ax_busy.plot(x, emp, "o-", color="#1E88E5", label="эмпирика")
        self.ax_busy.plot(
            x, self.th["busy"], "s--", color="#EF5350", label="теория"
        )
        self.ax_busy.set_xticks(x)
        self.ax_busy.set_xlabel("занято бариста")
        self.ax_busy.set_ylabel("вероятность")
        self.ax_busy.set_title("Полигон: занятые бариста", fontsize=10)
        self.ax_busy.legend(fontsize=7)
        self.ax_busy.grid(True, alpha=0.3)

        emp = c.queue_distribution()
        x = list(range(len(emp)))
        self.ax_queue.clear()
        self.ax_queue.plot(x, emp, "o-", color="#43A047", label="эмпирика")
        self.ax_queue.plot(
            x, self.th["queue"], "s--", color="#EF5350", label="теория"
        )
        self.ax_queue.set_xticks(x)
        self.ax_queue.set_xlabel("клиентов в очереди")
        self.ax_queue.set_title("Полигон: длина очереди", fontsize=10)
        self.ax_queue.legend(fontsize=7)
        self.ax_queue.grid(True, alpha=0.3)

        self.ax_wait.clear()
        if len(c.waits) > 20:
            centers, heights, width = histogram(
                c.waits, 20, max(max(c.waits), 0.1)
            )
            self.ax_wait.bar(
                centers, heights, width=width * 0.9, color="#42A5F5"
            )
        self.ax_wait.set_xlabel("время в очереди, мин")
        self.ax_wait.set_title("Гистограмма: ожидание", fontsize=10)
        self.ax_wait.grid(True, axis="y", alpha=0.3)

        self.canvas_fig.draw()

    def fill_table(self):
        c = self.cafe
        busy = c.busy_distribution()
        queue = c.queue_distribution()

        idle_emp = busy[0]
        load_emp = sum(k * busy[k] for k in range(len(busy))) / len(c.baristas)
        Lq_emp = sum(k * queue[k] for k in range(len(queue)))
        Wq_emp = sum(c.waits) / len(c.waits) if c.waits else 0.0
        refuse_emp = c.refused / c.came if c.came > 0 else 0.0
        giveup_emp = c.gave_up / c.came if c.came > 0 else 0.0

        nu = 1.0 / c.patience
        giveup_th = nu * self.th["Lq"] / c.lam

        rows = [
            ("Доля времени полного простоя", idle_emp, self.th["idle"]),
            ("Средняя загрузка бариста", load_emp, self.th["load"]),
            ("Средняя длина очереди", Lq_emp, self.th["Lq"]),
            ("Среднее время в очереди, мин", Wq_emp, self.th["Wq"]),
            ("Вероятность отказа (нет мест)", refuse_emp, self.th["p_refuse"]),
            ("Доля не дождавшихся", giveup_emp, giveup_th),
        ]
        for i, (name, e, t) in enumerate(rows):
            self.table.item(
                str(i),
                values=(name, "%.4f" % e, "%.4f" % t, "%.4f" % abs(e - t)),
            )


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


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
