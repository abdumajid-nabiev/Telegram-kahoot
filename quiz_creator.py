# quiz_creator.py
import os, json, uuid
from telegram import Update
from telegram.ext import ContextTypes

quiz_sessions = {}

async def createquiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    quiz_sessions[user_id] = {"step": 0, "questions": []}
    await update.message.reply_text("🧠 Let's create a new quiz!\nSend the quiz title:")

async def handle_quiz_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in quiz_sessions:
        return

    session = quiz_sessions[user_id]
    step = session["step"]

    if step == 0:
        session["title"] = update.message.text
        session["step"] += 1
        await update.message.reply_text("How many questions?")
    elif step == 1:
        try:
            session["count"] = int(update.message.text)
            session["step"] += 1
            session["q_index"] = 0
            session["current"] = {}
            await update.message.reply_text("Question 1: Send text or image.")
        except:
            await update.message.reply_text("❌ Invalid number. Try again.")
    elif step == 2:
        msg = update.message
        current = session["current"]
        if msg.photo:
            file = await msg.photo[-1].get_file()
            path = f"data/quizzes/static/{uuid.uuid4()}.jpg"
            await file.download_to_drive(path)
            current["question"] = path
            current["is_image"] = True
        else:
            current["question"] = msg.text
            current["is_image"] = False
        session["step"] += 1
        await update.message.reply_text("Now send the options separated by commas (e.g. A,B,C,D)")
    elif step == 3:
        options = [x.strip() for x in update.message.text.split(",")]
        if len(options) < 2:
            await update.message.reply_text("❌ Must be at least 2 options.")
            return
        session["current"]["options"] = options
        session["step"] += 1
        await update.message.reply_text("Which is the correct answer (exactly as one of the options)?")
    elif step == 4:
        ans = update.message.text.strip()
        if ans not in session["current"]["options"]:
            await update.message.reply_text("❌ Answer must match one of the options.")
            return
        session["current"]["answer"] = ans
        session["step"] += 1
        await update.message.reply_text("Set time limit in seconds (e.g. 20)")
    elif step == 5:
        try:
            limit = int(update.message.text)
            session["current"]["time_limit"] = limit
            session["questions"].append(session["current"])
            session["q_index"] += 1
            if session["q_index"] >= session["count"]:
                # Done!
                filename = f"data/quizzes/{session['title'].replace(' ', '_')}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(session["questions"], f, indent=2, ensure_ascii=False)
                del quiz_sessions[user_id]
                await update.message.reply_text(f"✅ Quiz saved as {filename}")
            else:
                session["step"] = 2
                session["current"] = {}
                await update.message.reply_text(f"Question {session['q_index']+1}: Send text or image.")
        except:
            await update.message.reply_text("❌ Invalid time. Enter an integer.")