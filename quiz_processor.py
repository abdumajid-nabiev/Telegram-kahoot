import os
import json
import pandas as pd
import random
from datetime import datetime
import re

QUIZ_DIR = "data/quizzes"
os.makedirs(QUIZ_DIR, exist_ok=True)

with open("data/wordbank.json", "r", encoding="utf-8") as f:
    WORD_BANK = json.load(f)

def generate_distractors(correct_answer, qtype):
    candidates = [w for w in WORD_BANK.get(qtype, []) if w != correct_answer]
    if len(candidates) < 3:
        return candidates
    return random.sample(candidates, 3)

def convert_file_to_quiz(file_path, time_limit=10, quiz_name=None):
    df = pd.read_csv(file_path) if file_path.endswith(".csv") else pd.read_excel(file_path)

    quiz = []
    for i, row in df.iterrows():
        question = str(row.get("Q", "") or row.get("Question", "")).strip()
        correct = str(row.get("A", "") or row.get("Answer", "")).strip()
        qtype = (row.get("Type", "") or row.get("type", "")).strip().lower()

        options_str = str(row.get("Options", "")).strip()
        options = [opt.strip() for opt in options_str.split(",") if opt.strip()] if options_str else []

        # If no or few options, generate distractors from WORD_BANK
        if len(options) < 4:
            distractors = generate_distractors(correct, qtype)
            options = distractors + [correct]
        else:
            if correct not in options:
                options.append(correct)

        # Ensure max 4 options, shuffle
        options = options[:4]
        random.shuffle(options)

        quiz.append({
            "text": question,
            "answer": correct,
            "options": options,
            "time_limit": int(time_limit)
        })

    if not quiz_name:
        quiz_name = datetime.now().strftime('%Y%m%d_%H%M%S_quiz')
    else:
        quiz_name = re.sub(r'[^\w\-_ ]', '', quiz_name).strip().replace(' ', '_')

    filename = f"{quiz_name}.json"
    filepath = os.path.join(QUIZ_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(quiz, f, ensure_ascii=False, indent=2)

    return filename
