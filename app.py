import os
import json
import random
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import pandas as pd

app = Flask(__name__)
app.secret_key = 'super-secret'

UPLOAD_FOLDER = 'uploads'
QUIZ_FOLDER = 'data/quizzes'
ALLOWED_EXTENSIONS = {'csv', 'xlsx'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(QUIZ_FOLDER, exist_ok=True)

word_bank = {
    'v': ['먹다', '자다', '가다', '일어나다', '만나다', '일하다', '오다'],
    'n': ['학교', '책상', '가방', '사람', '음식', '동물', '도시'],
    'a': ['빠른', '느린', '예쁜', '조용한', '시끄러운', '밝은'],
    'adv': ['빨리', '조용히', '천천히', '자주', '항상', '가끔']
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_distractors(correct_answer, qtype):
    candidates = [w for w in word_bank.get(qtype, []) if w != correct_answer]
    return random.sample(candidates, min(3, len(candidates)))

@app.route('/')
def index():
    return redirect(url_for('upload_quiz'))

@app.route('/upload', methods=['GET', 'POST'])
def upload_quiz():
    if request.method == 'POST':
        file = request.files.get('file')
        quiz_name = request.form.get('quiz_name', 'quiz')

        if not file or not allowed_file(file.filename):
            flash('Upload a valid .csv or .xlsx file')
            return redirect(request.url)

        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        return render_template('time_limit.html', quiz_name=quiz_name, filepath=filepath)

    return render_template('upload.html')

@app.route('/preview', methods=['POST'])
def preview_quiz():
    time_limit = int(request.form.get('time_limit', 7))
    quiz_name = request.form.get('quiz_name', 'quiz')
    filepath = request.form.get('filepath')

    if not os.path.exists(filepath):
        flash('File not found. Please re-upload.')
        return redirect(url_for('upload_quiz'))

    if filepath.endswith('.csv'):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    df.columns = [c.strip().lower() for c in df.columns]
    if not {'q', 'a', 'type'}.issubset(df.columns):
        flash('File must include Q, A, and Type columns')
        return redirect(url_for('upload_quiz'))

    quiz = []
    for _, row in df.iterrows():
        q, a, t = row['q'], row['a'], row['type'].strip().lower()
        distractors = generate_distractors(a, t)
        options = distractors + [a]
        random.shuffle(options)

        quiz.append({
            'text': str(q),
            'answer': str(a),
            'options': options,
            'time_limit': time_limit
        })

    return render_template('preview.html', quiz=quiz, quiz_name=quiz_name)

@app.route('/save_quiz', methods=['POST'])
def save_quiz():
    quiz_json = request.form.get('quiz_json')
    quiz_name = secure_filename(request.form.get('quiz_name', 'quiz'))

    if not quiz_json:
        flash('No quiz data to save.')
        return redirect(url_for('upload_quiz'))

    with open(os.path.join(QUIZ_FOLDER, quiz_name + '.json'), 'w', encoding='utf-8') as f:
        f.write(quiz_json)

    flash(f'Saved quiz: {quiz_name}.json')
    return redirect(url_for('upload_quiz'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
