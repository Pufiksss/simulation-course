import random
import tkinter as tk
from tkinter import messagebox

answers = [
    "Бесспорно!",
    "Это так!",
    "Без сомнений!",
    "Определённо да!",
    "Можешь быть уверен!",
    "Мне кажется — да!",
    "Вероятнее всего!",
    "Хорошие перспективы!",
    "Знаки говорят — да!",
    "Да!",
    "Пока не ясно, попробуй снова",
    "Спроси позже!",
    "Лучше не говорить",
    "Сейчас нельзя предсказать",
    "Сосредоточься и спроси снова",
    "Нет!",
]

probabilities = []
i = 0
while i < 16:
    probabilities.append(1 / 16)
    i = i + 1


def generate_group_event():
    alpha = random.random()

    cumulative = 0.0
    k = 0
    while k < len(probabilities):
        cumulative += probabilities[k]
        if alpha < cumulative:
            return k
        k = k + 1

    return len(probabilities) - 1


def on_ask():
    question = entry_question.get()

    if question == "":
        messagebox.showwarning("Ошибка", "Введите вопрос!")
        return

    k = generate_group_event()
    answer = answers[k]
    label_answer.config(text=answer)


def on_stats():
    N = 10000
    statistics = []
    k = 0
    while k < len(answers):
        statistics.append(0)
        k = k + 1

    n = 0
    while n < N:
        k = generate_group_event()
        statistics[k] = statistics[k] + 1
        n = n + 1

    frequency = []
    k = 0
    while k < len(answers):
        freq = statistics[k] / N
        frequency.append(freq)
        k = k + 1

    msg = "Статистика за " + str(N) + " испытаний:\n\n"
    k = 0
    while k < len(answers):
        msg = msg + answers[k] + "\n"
        msg = (
            msg + "  теор: 0.0625   эмп: " + str(round(frequency[k], 4)) + "\n"
        )
        k = k + 1

    stats_window = tk.Toplevel(window)
    stats_window.title("Статистика")
    stats_window.geometry("420x500")
    stats_window.configure(bg="#1e1e2e")

    text_widget = tk.Text(
        stats_window,
        font=("Courier New", 10),
        bg="#313244",
        fg="#cdd6f4",
        relief="flat",
        padx=10,
        pady=10,
    )
    text_widget.insert("1.0", msg)
    text_widget.config(state="disabled")
    text_widget.pack(fill="both", expand=True, padx=10, pady=10)


window = tk.Tk()
window.title("Шар предсказаний")
window.geometry("440x360")
window.resizable(False, False)
window.configure(bg="#1e1e2e")

label_title = tk.Label(
    window,
    text="🎱 Шар предсказаний",
    font=("Courier New", 20, "bold"),
    bg="#1e1e2e",
    fg="#cdd6f4",
)
label_title.pack(pady=(20, 5))

label_sub = tk.Label(
    window,
    text="Magic 8-Ball",
    font=("Courier New", 11),
    bg="#1e1e2e",
    fg="#6c7086",
)
label_sub.pack(pady=(0, 15))

label_q = tk.Label(
    window,
    text="Задайте вопрос шару:",
    font=("Courier New", 11),
    bg="#1e1e2e",
    fg="#a6adc8",
)
label_q.pack()

entry_question = tk.Entry(
    window,
    font=("Courier New", 11),
    width=38,
    bg="#313244",
    fg="#cdd6f4",
    insertbackground="#cdd6f4",
    relief="flat",
)
entry_question.insert(0, "Сдам ли я экзамен?")
entry_question.pack(pady=(4, 15), ipady=6)

frame_buttons = tk.Frame(window, bg="#1e1e2e")
frame_buttons.pack()

btn_ask = tk.Button(
    frame_buttons,
    text="Спросить",
    font=("Courier New", 12, "bold"),
    bg="#cba6f7",
    fg="#1e1e2e",
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2",
    command=on_ask,
)
btn_ask.pack(side="left", padx=8)

btn_stats = tk.Button(
    frame_buttons,
    text="Статистика",
    font=("Courier New", 12),
    bg="#313244",
    fg="#cdd6f4",
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2",
    command=on_stats,
)
btn_stats.pack(side="left", padx=8)

# Ответ
label_answer = tk.Label(
    window,
    text="...",
    font=("Courier New", 22, "bold"),
    bg="#1e1e2e",
    fg="#f38ba8",
    wraplength=380,
)
label_answer.pack(pady=25)

window.mainloop()
