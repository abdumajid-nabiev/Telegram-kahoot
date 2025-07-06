# import json
# import os
# from utils import format_time
# from telegram import InlineKeyboardButton, InlineKeyboardMarkup
# from telegram.ext import ContextTypes, CallbackContext
# from utils import stop_timer
# from telegram.ext import ApplicationBuilder
# from quiz_handler import qh_app
# qh_app = None  # ✅ Allow it to be set later


# PLAYERS_FILE = "data/players.json"
# players = {}
# sessions = {}
# multisessions = {}
# answered_counts = {}

# # Load/save

# def load_players():
#     global players
#     if os.path.exists(PLAYERS_FILE):
#         with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
#             players = json.load(f)
#         for uid, p in players.items():
#             p.setdefault("name", "Unknown")
#             p.setdefault("score", 0)
#     else:
#         players = {}

# def save_players():
#     os.makedirs(os.path.dirname(PLAYERS_FILE), exist_ok=True)
#     with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
#         json.dump(players, f, indent=2)

# # Per-quiz session

# def start_session(user_id, total_questions):
#     sessions[user_id] = {
#         "questions": total_questions,
#         "answered": 0,
#         "correct": 0,
#         "time": 0.0,
#         "score": 0
#     }

# def add_player(user_id, name):
#     load_players()
#     uid = str(user_id)
#     if uid not in players:
#         players[uid] = {"name": name, "score": 0}
#         save_players()

# def update_player_answer(user_id, is_correct, elapsed):
#     load_players()
#     uid = str(user_id)
#     if uid in players and is_correct:
#         players[uid]["score"] += max(0, 100 - int(elapsed))
#         save_players()
#     sess = sessions.get(user_id)
#     if sess:
#         sess["answered"] += 1
#         if is_correct:
#             sess["correct"] += 1
#             sess["score"] += max(0, 100 - int(elapsed))
#         sess["time"] += elapsed

# def get_rankings(current_user_id=None):
#     sorted_users = sorted(
#         sessions.items(), key=lambda x: (-x[1]["score"], x[1]["time"])
#     )
#     output = "🏆 Live Rankings:\n"
#     for i, (uid, sess) in enumerate(sorted_users, 1):
#         name = players.get(str(uid), {}).get("name", "Unknown")
#         score = sess.get("score", 0)
#         correct = sess.get("correct", 0)
#         total_q = sess.get("questions", 1)
#         total_time = sess.get("time", 0.0)
#         accuracy = int(correct * 100 / total_q) if total_q else 0
#         total_time_str = f"{int(total_time)}s"
#         line = f"{i}. {name} - {score} pts - {accuracy}% correct - {total_time_str} total"
#         if current_user_id and uid == current_user_id:
#             line = "👉 " + line
#         output += line + "\n"
#     return output

# # Multiplayer Answer Handler

# async def handle_multi_answer(update, context):
#     query = update.callback_query
#     await query.answer()
#     _, code, answer = query.data.split("|", 2)
#     sess = multisessions.get(code)
#     qidx = sess["q_index"]
#     q = sess["quiz"][qidx]
#     user_id = query.from_user.id

#     elapsed = stop_timer(context.user_data["timer"])
#     correct = (answer == q["answer"])
#     score = max(0, 100 - int(elapsed)) if correct else 0
#     sess["answers"][user_id].append({"correct": correct, "score": score, "time": elapsed})

#     try:
#         await query.edit_message_reply_markup()
#     except:
#         pass

#     answered_counts[code] += 1
#     count = answered_counts[code]
#     bot = context.bot
#     for pid in sess["participants"]:
#         msg_id = sess["message_ids"].get(pid)
#         if msg_id:
#             q_text = q.get("text", "")
#             await bot.edit_message_text(
#                 chat_id=pid,
#                 message_id=msg_id,
#                 text=f"❓ Q{qidx+1}: {q_text}\n✅ Answered People: {count}"
#             )

#     if all(len(sess["answers"][pid]) == qidx + 1 for pid in sess["participants"]):
#         sess["q_index"] += 1

#         # ✅ Send live rankings to channel
#         rankings = []
#         for pid in sess["participants"]:
#             p = sess["answers"][pid]
#             pts = sum(a["score"] for a in p)
#             correct = sum(1 for a in p if a["correct"])
#             total = len(p)
#             acc = int((correct / total) * 100) if total > 0 else 0
#             t = int(sum(a["time"] for a in p))
#             name = (await bot.get_chat(pid)).first_name
#             rankings.append((pts, f"{name}: {pts} pts - {acc}% correct - {t}s"))

#         rankings.sort(reverse=True)
#         rank_text = "\n".join([r[1] for r in rankings])
#         await bot.send_message(chat_id="@korai_verse", text=f"📢 Live Rankings After Q{qidx+1}:\n{rank_text}")

#         await _broadcast_question(code)

# async def _broadcast_question(code):
#     sess = multisessions[code]
#     answered_counts[code] = 0
#     qidx = sess["q_index"]
#     quiz = sess["quiz"]
#     from telegram import Bot


#     if qidx >= len(quiz):
#         summary = []
#         for pid in sess["participants"]:
#             pts = sum(a["score"] for a in sess["answers"][pid])
#             corr = sum(1 for a in sess["answers"][pid] if a["correct"])
#             total = len(sess["answers"][pid])
#             summary.append(f"{(await context.bot.get_chat(pid)).first_name}: {pts}pts, {corr}/{total}")
#         text = "🎉 Session finished!\n" + "\n".join(summary)
#         for pid in sess["participants"]:
#             await bot.send_message(pid, text)
#         del multisessions[code]
#         return

#     q = quiz[qidx]
#     sess["message_ids"] = {}
#     buttons = [[InlineKeyboardButton(opt, callback_data=f"MULTI|{code}|{opt}")] for opt in q["options"]]

#     for pid in sess["participants"]:
#         if q.get("is_image"):
#             with open(q["question"], "rb") as img:
#                 msg = await bot.send_photo(
#                     pid, img,
#                     caption=f"❓ Q{qidx+1}: {q.get('text', '')}\n✅ Answered People: 0",
#                     reply_markup=InlineKeyboardMarkup(buttons)
#                 )
#         else:
#             msg = await bot.send_message(
#                 pid,
#                 f"❓ Q{qidx+1}: {q.get('text', '')}\n✅ Answered People: 0",
#                 reply_markup=InlineKeyboardMarkup(buttons)
#             )
#         sess["message_ids"][pid] = msg.message_id


import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from utils import stop_timer, format_time

PLAYERS_FILE = "data/players.json"
players = {}
sessions = {}
multisessions = {}
answered_counts = {}

# ------------------------
# Player Management
# ------------------------

def load_players():
    global players
    if os.path.exists(PLAYERS_FILE):
        with open(PLAYERS_FILE, "r", encoding="utf-8") as f:
            players = json.load(f)
        for uid, p in players.items():
            p.setdefault("name", "Unknown")
            p.setdefault("score", 0)
    else:
        players = {}

def save_players():
    os.makedirs(os.path.dirname(PLAYERS_FILE), exist_ok=True)
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(players, f, indent=2)

def start_session(user_id, total_questions):
    sessions[user_id] = {
        "questions": total_questions,
        "answered": 0,
        "correct": 0,
        "time": 0.0,
        "score": 0
    }

def add_player(user_id, name):
    load_players()
    uid = str(user_id)
    if uid not in players:
        players[uid] = {"name": name, "score": 0}
        save_players()

def update_player_answer(user_id, is_correct, elapsed):
    load_players()
    uid = str(user_id)
    if uid in players and is_correct:
        players[uid]["score"] += max(0, 100 - int(elapsed))
        save_players()
    sess = sessions.get(user_id)
    if sess:
        sess["answered"] += 1
        if is_correct:
            sess["correct"] += 1
            sess["score"] += max(0, 100 - int(elapsed))
        sess["time"] += elapsed

def get_rankings(current_user_id=None):
    sorted_users = sorted(
        sessions.items(), key=lambda x: (-x[1]["score"], x[1]["time"])
    )
    output = "🏆 Live Rankings:\n"
    for i, (uid, sess) in enumerate(sorted_users, 1):
        name = players.get(str(uid), {}).get("name", "Unknown")
        score = sess.get("score", 0)
        correct = sess.get("correct", 0)
        total_q = sess.get("questions", 1)
        total_time = sess.get("time", 0.0)
        accuracy = int(correct * 100 / total_q) if total_q else 0
        total_time_str = f"{int(total_time)}s"
        line = f"{i}. {name} - {score} pts - {accuracy}% correct - {total_time_str} total"
        if current_user_id and uid == current_user_id:
            line = "👉 " + line
        output += line + "\n"
    return output

# ------------------------
# Multiplayer Answer Handler
# ------------------------

async def handle_multi_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    _, code, answer = query.data.split("|", 2)
    sess = multisessions.get(code)
    qidx = sess["q_index"]
    q = sess["quiz"][qidx]
    user_id = query.from_user.id

    elapsed = stop_timer(context.user_data["timer"])
    correct = (answer == q["answer"])
    score = max(0, 100 - int(elapsed)) if correct else 0
    sess["answers"][user_id].append({"correct": correct, "score": score, "time": elapsed})

    try:
        await query.edit_message_reply_markup()
    except:
        pass

    answered_counts[code] += 1
    count = answered_counts[code]

    for pid in sess["participants"]:
        msg_id = sess["message_ids"].get(pid)
        if msg_id:
            q_text = q.get("text", "")
            await context.bot.edit_message_text(
                chat_id=pid,
                message_id=msg_id,
                text=f"❓ Q{qidx+1}: {q_text}\n✅ Answered People: {count}"
            )

    # Check if all participants answered
    if all(len(sess["answers"][pid]) == qidx + 1 for pid in sess["participants"]):
        sess["q_index"] += 1

        # Send live rankings
        rankings = []
        for pid in sess["participants"]:
            p = sess["answers"][pid]
            pts = sum(a["score"] for a in p)
            correct = sum(1 for a in p if a["correct"])
            total = len(p)
            acc = int((correct / total) * 100) if total > 0 else 0
            t = int(sum(a["time"] for a in p))
            name = (await context.bot.get_chat(pid)).first_name
            rankings.append((pts, f"{name}: {pts} pts - {acc}% correct - {t}s"))

        rankings.sort(reverse=True)
        rank_text = "\n".join([r[1] for r in rankings])
        await context.bot.send_message(chat_id="@korai_verse", text=f"📢 Live Rankings After Q{qidx+1}:\n{rank_text}")

        await _broadcast_question(code, context)

# ------------------------
# Broadcast Question
# ------------------------

async def _broadcast_question(code: str, context: ContextTypes.DEFAULT_TYPE):
    sess = multisessions[code]
    answered_counts[code] = 0
    qidx = sess["q_index"]
    quiz = sess["quiz"]

    if qidx >= len(quiz):
        # Quiz finished
        summary = []
        for pid in sess["participants"]:
            pts = sum(a["score"] for a in sess["answers"][pid])
            corr = sum(1 for a in sess["answers"][pid] if a["correct"])
            total = len(sess["answers"][pid])
            summary.append(f"{(await context.bot.get_chat(pid)).first_name}: {pts}pts, {corr}/{total}")
        text = "🎉 Session finished!\n" + "\n".join(summary)
        for pid in sess["participants"]:
            await context.bot.send_message(pid, text)
        del multisessions[code]
        return

    q = quiz[qidx]
    sess["message_ids"] = {}
    buttons = [[InlineKeyboardButton(opt, callback_data=f"MULTI|{code}|{opt}")] for opt in q["options"]]

    for pid in sess["participants"]:
        if q.get("is_image"):
            with open(q["question"], "rb") as img:
                msg = await context.bot.send_photo(
                    pid, img,
                    caption=f"❓ Q{qidx+1}: {q.get('text', '')}\n✅ Answered People: 0",
                    reply_markup=InlineKeyboardMarkup(buttons)
                )
        else:
            msg = await context.bot.send_message(
                pid,
                f"❓ Q{qidx+1}: {q.get('text', '')}\n✅ Answered People: 0",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        sess["message_ids"][pid] = msg.message_id
