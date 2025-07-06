import json
import random
import tkinter as tk
from tkinter import messagebox, filedialog

# Korean distractors pool
korean_words = ["서울", "토끼", "무지개", "고양이", "물고기", "바나나", "호랑이", "기린", "비행기", "학교"]

quiz = []

def add_question():
    q_text = question_entry.get()
    correct = correct_entry.get()
    time_limit = int(time_entry.get() or 10)

    if not q_text or not correct:
        messagebox.showerror("Error", "Fill in both question and correct answer")
        return

    wrong_choices = random.sample([w for w in korean_words if w != correct], 3)
    options = wrong_choices + [correct]
    random.shuffle(options)

    quiz.append({
        "text": q_text,
        "answer": correct,
        "options": options,
        "time_limit": time_limit
    })

    question_entry.delete(0, tk.END)
    correct_entry.delete(0, tk.END)

    messagebox.showinfo("Added", f"Question added! Total: {len(quiz)}")

def save_quiz():
    if not quiz:
        messagebox.showerror("Error", "No questions to save!")
        return

    filename = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json")],
        initialdir="data/quizzes"
    )

    if filename:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(quiz, f, indent=2, ensure_ascii=False)
        messagebox.showinfo("Saved", f"Quiz saved to {filename}")
        quiz.clear()

app = tk.Tk()
app.title("Quiz Creator")

tk.Label(app, text="Question:").pack()
question_entry = tk.Entry(app, width=50)
question_entry.pack()

tk.Label(app, text="Correct Answer (English):").pack()
correct_entry = tk.Entry(app, width=50)
correct_entry.pack()

tk.Label(app, text="Time Limit (seconds):").pack()
time_entry = tk.Entry(app, width=10)
time_entry.insert(0, "7")
time_entry.pack()

tk.Button(app, text="➕ Add Question", command=add_question).pack(pady=5)
tk.Button(app, text="💾 Save Quiz", command=save_quiz).pack()

app.mainloop()
