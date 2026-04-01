import random
import tkinter as tk
from tkinter import messagebox


def random_event(p):
    alpha = random.random()
    if alpha < p:
        return True
    else:
        return False


def on_click():
    question = entry_question.get()
    p_text = entry_prob.get()

    if question == "":
        messagebox.showwarning("Ошибка", "Введите вопрос!")
        return

    try:
        p = float(p_text)
    except:
        messagebox.showwarning("Ошибка", "Вероятность должна быть числом!")
        return

    if p < 0 or p > 1:
        messagebox.showwarning("Ошибка", "Вероятность должна быть от 0 до 1!")
        return

    result = random_event(p)

    if result:
        label_answer.config(text="ДА!", fg="#27ae60")
    else:
        label_answer.config(text="НЕТ!", fg="#e74c3c")


def on_stats():
    p_text = entry_prob.get()

    try:
        p = float(p_text)
    except:
        messagebox.showwarning("Ошибка", "Вероятность должна быть числом!")
        return

    if p < 0 or p > 1:
        messagebox.showwarning("Ошибка", "Вероятность должна быть от 0 до 1!")
        return

    # Статистическая обработка
    N = 10000
    yes_count = 0
    i = 0
    while i < N:
        if random_event(p):
            yes_count = yes_count + 1
        i = i + 1

    freq = yes_count / N

    msg = "Статистика за " + str(N) + " испытаний:\n"
    msg = msg + "Теоретическая вероятность: " + str(p) + "\n"
    msg = msg + "Эмпирическая вероятность:  " + str(round(freq, 4))
    messagebox.showinfo("Статистика", msg)


# --- Создание окна ---
window = tk.Tk()
window.title("Скажи ДА или НЕТ")
window.geometry("420x320")
window.resizable(False, False)
window.configure(bg="#1e1e2e")

# Заголовок
label_title = tk.Label(
    window,
    text="Скажи ДА или НЕТ",
    font=("Courier New", 18, "bold"),
    bg="#1e1e2e",
    fg="#cdd6f4",
)
label_title.pack(pady=(20, 10))

# Поле для вопроса
label_q = tk.Label(
    window,
    text="Ваш вопрос:",
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
entry_question.insert(0, "Пойти сегодня в университет?")
entry_question.pack(pady=(2, 10), ipady=5)

# Поле для вероятности
label_p = tk.Label(
    window,
    text="Вероятность ДА (0..1):",
    font=("Courier New", 11),
    bg="#1e1e2e",
    fg="#a6adc8",
)
label_p.pack()

entry_prob = tk.Entry(
    window,
    font=("Courier New", 11),
    width=10,
    bg="#313244",
    fg="#cdd6f4",
    insertbackground="#cdd6f4",
    relief="flat",
    justify="center",
)
entry_prob.insert(0, "0.5")
entry_prob.pack(pady=(2, 15), ipady=5)

# Кнопки
frame_buttons = tk.Frame(window, bg="#1e1e2e")
frame_buttons.pack()

btn_ask = tk.Button(
    frame_buttons,
    text="Спросить",
    font=("Courier New", 12, "bold"),
    bg="#89b4fa",
    fg="#1e1e2e",
    relief="flat",
    padx=15,
    pady=6,
    cursor="hand2",
    command=on_click,
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

label_answer = tk.Label(
    window,
    text="",
    font=("Courier New", 36, "bold"),
    bg="#1e1e2e",
    fg="#cdd6f4",
)
label_answer.pack(pady=15)

window.mainloop()
