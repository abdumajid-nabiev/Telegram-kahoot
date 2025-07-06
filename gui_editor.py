# gui_editor.py
from flask import Flask, jsonify, request, send_from_directory
import os, json

app = Flask(__name__, static_folder="gui", static_url_path="")
QUIZ_DIR = "data/quizzes"

@app.route("/")
def index():
    return send_from_directory("gui", "index.html")

@app.route("/api/quizzes")
def list_quizzes():
    return jsonify([f for f in os.listdir(QUIZ_DIR) if f.endswith(".json")])

@app.route("/api/quiz/<filename>")
def load_quiz(filename):
    with open(os.path.join(QUIZ_DIR, filename), encoding="utf-8") as f:
        return jsonify(json.load(f))

@app.route("/api/quiz/<filename>", methods=["POST"])
def save_quiz(filename):
    data = request.get_json()
    with open(os.path.join(QUIZ_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return jsonify({"status":"ok"})

if __name__ == "__main__":
    app.run(port=5001)
