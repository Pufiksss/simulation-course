import random
import tkinter as tk
from tkinter import messagebox, ttk

ANSWERS = [
    "Определённо да",
    "Скорее всего да",
    "Скорее нет",
    "Определённо нет",
    "Спроси позже",
    "Не рассчитывай на это",
    "Знаки указывают — да",
    "Очень сомнительно",
]


def generate_event(probs):
    r = random.random()
    i = 0
    while i < len(probs):
        r -= probs[i]
        if r < 0:
            return i, r
        i += 1
    return len(probs) - 1, r


# 5.1
class YesNoApp(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padx=24, pady=20)

        tk.Label(self, text="Вопрос:").grid(row=0, column=0, sticky="w")
        self.entry = tk.Entry(self, width=44)
        self.entry.grid(
            row=1, column=0, columnspan=2, sticky="ew", pady=(0, 12)
        )

        tk.Label(self, text="Вероятность «да»:").grid(
            row=2, column=0, sticky="w"
        )
        self.prob_var = tk.DoubleVar(value=0.5)
        self.prob_label = tk.Label(self, text="0.50", width=5, anchor="w")
        self.prob_label.grid(row=2, column=1, sticky="w")

        self.slider = ttk.Scale(
            self,
            from_=0,
            to=1,
            variable=self.prob_var,
            orient="horizontal",
            length=360,
            command=lambda v: self.prob_label.config(text=f"{float(v):.2f}"),
        )
        self.slider.grid(row=3, column=0, columnspan=2, pady=(4, 16))

        tk.Button(self, text="Спросить", width=16, command=self.ask).grid(
            row=4, column=0, columnspan=2
        )

        self.answer_var = tk.StringVar(value="...")
        self.answer_label = tk.Label(
            self,
            textvariable=self.answer_var,
            font=("Arial", 28, "bold"),
            width=10,
        )
        self.answer_label.grid(row=5, column=0, columnspan=2, pady=16)

        self.trace_var = tk.StringVar()
        tk.Label(
            self, textvariable=self.trace_var, font=("Courier", 10), fg="gray"
        ).grid(row=6, column=0, columnspan=2)

    def ask(self):
        p = self.prob_var.get()
        r = random.random()
        yes = r < p

        self.answer_var.set("ДА!" if yes else "НЕТ!")
        self.answer_label.config(fg="green" if yes else "red")
        self.trace_var.set(f"r = {r:.4f}   p = {p:.2f}")


# 5.2
class Magic8App(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, padx=24, pady=20)

        tk.Label(self, text="Ваш вопрос:").grid(
            row=0, column=0, columnspan=3, sticky="w"
        )
        self.entry = tk.Entry(self, width=44)
        self.entry.grid(
            row=1, column=0, columnspan=3, sticky="ew", pady=(0, 14)
        )

        tk.Label(self, text="Ответ", font=("Arial", 10, "bold")).grid(
            row=2, column=0, sticky="w"
        )
        tk.Label(self, text="Вероятность", font=("Arial", 10, "bold")).grid(
            row=2, column=1, sticky="w", padx=(12, 0)
        )

        self.prob_entries = []
        p = 1 / len(ANSWERS)

        for i, answer in enumerate(ANSWERS):
            tk.Label(self, text=answer, width=26, anchor="w").grid(
                row=3 + i, column=0, sticky="w", pady=2
            )
            var = tk.StringVar(value=str(round(p, 4)))
            e = tk.Entry(self, textvariable=var, width=8)
            e.grid(row=3 + i, column=1, sticky="w", padx=(12, 0), pady=2)
            self.prob_entries.append(var)

        self.ball_label = tk.Label(
            self, text="🎱", font=("Arial", 48), cursor="hand2"
        )
        self.ball_label.grid(row=2, column=2, rowspan=5, padx=(24, 0))
        self.ball_label.bind("<Button-1>", lambda e: self.shake())

        tk.Label(
            self, text="нажмите на шар", fg="gray", font=("Arial", 9)
        ).grid(row=7, column=2, padx=(24, 0))

        self.answer_var = tk.StringVar(value="")
        tk.Label(
            self,
            textvariable=self.answer_var,
            font=("Arial", 14, "bold"),
            wraplength=160,
            justify="center",
        ).grid(row=8, column=2, rowspan=3, padx=(24, 0), pady=8)

        self.trace_var = tk.StringVar()
        tk.Label(
            self, textvariable=self.trace_var, font=("Courier", 9), fg="gray"
        ).grid(row=11, column=2, padx=(24, 0))

    def get_probs(self):
        probs = [float(v.get()) for v in self.prob_entries]
        total = sum(probs)

        if total != 1:
            messagebox.showerror(
                "Ошибка", f"Сумма вероятностей должна = 1.\nСейчас: {total:.4f}"
            )
            return None

        return probs

    def shake(self):
        self.ball_label.config(text="💫")
        self.after(200, self._reveal)

    def _reveal(self):
        self.ball_label.config(text="🎱")

        probs = self.get_probs()
        if probs is None:
            return

        i, r = generate_event(probs)
        self.answer_var.set(ANSWERS[i])
        self.trace_var.set(f"r = {r:.4f}   i = {i}")


root = tk.Tk()
root.resizable(False, False)

notebook = ttk.Notebook(root)
notebook.pack(fill="both", expand=True)

notebook.add(YesNoApp(notebook), text="  Лаб 5.1 — Да / Нет  ")
notebook.add(Magic8App(notebook), text="  Лаб 5.2 — Magic 8-Ball  ")

root.mainloop()
