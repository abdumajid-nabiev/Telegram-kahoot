import os
import json
import asyncio
import random
import telegram
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, ConversationHandler, filters
from telegram.error import BadRequest
from utils import start_timer, stop_timer  # If you have these helpers
from player_manager import add_player, update_player_answer, get_rankings, start_session
import random, string, json, os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from utils import stop_timer
from player_manager import add_player, update_player_answer, get_rankings, start_session, _broadcast_question  # ensure start_session is in player_manager
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import BadRequest
import asyncio
from utils import stop_timer
from player_manager import update_player_answer, get_rankings
import re
from typing import Any



QUIZ_DIR = "data/quizzes"
QUIZ_ORDER_FILE = os.path.join(QUIZ_DIR, "quiz_order.json")
quiz_data = []
QUIZ_PATH = None
SELECT_QUIZ, SELECT_QUESTION, EDIT_ACTION, EDIT_TEXT, EDIT_OPTIONS = range(5)
answered_counts = {}  # Key: session code, Value: int of users who answered current question


def normalize(s: Any) -> str:
    """
    Convert to string, strip whitespace, lowercase, remove
    zero‑width spaces, and collapse internal whitespace.
    """
    text = str(s)
    # remove any zero‑width or control chars
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    # collapse whitespace, strip ends
    text = re.sub(r'\s+', ' ', text).strip()
    return text.casefold()





async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rankings = get_rankings(user_id)
    await update.message.reply_text(rankings)

async def replay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    context.user_data["question_index"] = 0
    context.user_data["answered"] = False
    context.user_data["timer"] = start_timer()
    add_player(user_id, update.effective_user.first_name)
    await send_question(update, context)

def get_quiz_order():
    if not os.path.exists(QUIZ_ORDER_FILE):
        files = sorted([f for f in os.listdir(QUIZ_DIR) if f.endswith(".json")])
        with open(QUIZ_ORDER_FILE, "w", encoding="utf-8") as f:
            json.dump(files, f)
    with open(QUIZ_ORDER_FILE, encoding="utf-8") as f:
        return json.load(f)

def load_ordered_quizzes():
    files = [f for f in os.listdir(QUIZ_DIR) if f.endswith(".json")]
    if os.path.exists(QUIZ_ORDER_FILE):
        with open(QUIZ_ORDER_FILE, "r", encoding="utf-8") as f:
            saved_order = json.load(f)
        # Preserve only existing files
        ordered = [f for f in saved_order if f in files]
        unordered = [f for f in files if f not in ordered]
        return ordered + unordered
    return files

def save_quiz_order(file_list):
    with open(QUIZ_ORDER_FILE, "w", encoding="utf-8") as f:
        json.dump(file_list, f)


async def quizlist_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = load_ordered_quizzes()
    context.user_data["reorder_mode"] = False  # default

    buttons = [[InlineKeyboardButton(f"📝 {f}", callback_data=f"QUIZ_{f}")] for f in files]
    buttons.append([InlineKeyboardButton("🔁 Reorder quizzes", callback_data="ENTER_REORDER")])

    if update.message:
        await update.message.reply_text("📚 Select a quiz:", reply_markup=InlineKeyboardMarkup(buttons))
    elif update.callback_query:
        await update.callback_query.edit_message_text("📚 Select a quiz:", reply_markup=InlineKeyboardMarkup(buttons))

async def show_reorder_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    files = load_ordered_quizzes()
    context.user_data["reorder_mode"] = True

    buttons = []
    for f in files:
        buttons.append([
            InlineKeyboardButton(f"📝 {f}", callback_data=f"QUIZ_IGNORE"),
            InlineKeyboardButton("⬆️", callback_data=f"UP_{f}"),
            InlineKeyboardButton("⬇️", callback_data=f"DOWN_{f}")
        ])
    buttons.append([InlineKeyboardButton("✅ Done reordering", callback_data="EXIT_REORDER")])

    await update.callback_query.edit_message_text("🔧 Reorder quizzes:", reply_markup=InlineKeyboardMarkup(buttons))

async def handle_quizlist_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    files = load_ordered_quizzes()

    if data == "ENTER_REORDER":
        return await show_reorder_menu(update, context)

    elif data == "EXIT_REORDER":
        context.user_data["reorder_mode"] = False
        return await quizlist_command(update, context)

    if data.startswith("UP_") or data.startswith("DOWN_"):
        target = data.split("_", 1)[1]
        if target not in files:
            return
        idx = files.index(target)
        if data.startswith("UP_") and idx > 0:
            files[idx], files[idx - 1] = files[idx - 1], files[idx]
        elif data.startswith("DOWN_") and idx < len(files) - 1:
            files[idx], files[idx + 1] = files[idx + 1], files[idx]
        save_quiz_order(files)
        return await show_reorder_menu(update, context)

    elif data.startswith("QUIZ_") and not context.user_data.get("reorder_mode", False):
        return await select_quiz(update, context)


async def select_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global quiz_data, QUIZ_PATH
    query = update.callback_query
    await query.answer()
    filename = query.data.replace("QUIZ_", "")
    QUIZ_PATH = os.path.join(QUIZ_DIR, filename)

    with open(QUIZ_PATH, encoding="utf-8") as f:
        quiz_data = json.load(f)

    import random
    random.shuffle(quiz_data)
    for q in quiz_data:
        if isinstance(q.get("options"), list):
            random.shuffle(q["options"])

    user_id = query.from_user.id
    name = context.user_data.get("nickname") or query.from_user.first_name
    add_player(user_id, name)

    from player_manager import start_session
    start_session(user_id, len(quiz_data))

    context.user_data["question_index"] = 0
    context.user_data["timer"] = start_timer()
    context.user_data["answered"] = False
    context.user_data["user_id"] = user_id

    await send_question(update, context)

from itertools import zip_longest

def build_option_buttons(options, disabled=False, feedback=None):
    rows = []
    labels = []

    for opt in options:
        if feedback:
            user_answer, correct_answer, is_correct = feedback
            if opt == user_answer:
                label = f"{'✅' if is_correct else '❌'} {opt}"
            elif opt == correct_answer and not is_correct:
                label = f"💡 {opt}"
            else:
                label = opt
        else:
            label = opt
        labels.append(label)

    for left, right in zip_longest(*[iter(labels)]*2):
        row = []
        if left:
            row.append(InlineKeyboardButton(
                left, callback_data="DISABLED" if disabled else options[labels.index(left)]))
        if right:
            row.append(InlineKeyboardButton(
                right, callback_data="DISABLED" if disabled else options[labels.index(right)]))
        rows.append(row)

    return InlineKeyboardMarkup(rows)



async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data.get("question_index", 0)
    if index >= len(quiz_data):
        chat_id = update.effective_chat.id if hasattr(update, "effective_chat") else context.user_data.get("chat_id")
        await context.bot.send_message(
            chat_id=chat_id,
            text="🎉 *Quiz finished!*",
            parse_mode="Markdown"
        )
        return

    context.user_data["answered"] = False
    q = quiz_data[index]
    time_limit = q.get("time_limit", 30)
    context.user_data["timer"] = start_timer()

    # 2-column button layout
    reply_markup = build_option_buttons(q["options"])

    question_text = f"📖 *Q{index+1}:* {str(q['text']).strip()}\n⏳ *{time_limit} seconds*"


    chat_id = update.effective_chat.id if hasattr(update, "effective_chat") and update.effective_chat else context.user_data.get("chat_id")

    if q.get("is_image") and os.path.exists(q["question"]):
        with open(q["question"], "rb") as img:
            msg = await context.bot.send_photo(
                chat_id=chat_id,
                photo=img,
                caption=question_text,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        msg = await context.bot.send_message(
            chat_id=chat_id,
            text=question_text,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    context.user_data["current_message_id"] = msg.message_id
    context.user_data["chat_id"] = chat_id
    context.user_data["question_index"] = index
    context.user_data["time_limit"] = time_limit

    context.user_data["timer_task"] = context.application.create_task(
    countdown_timer(chat_id, msg.message_id, time_limit)
)


async def user_answer_received(context):
    while not context.user_data.get("answered", False):
        await asyncio.sleep(0.5)

def safe_strip(x):
    if isinstance(x, str):
        return x.strip()
    else:
        return str(x).strip()

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Prevent double submissions
    if context.user_data.get("answered", False):
        return

    context.user_data["answered"] = True
    # Cancel any running countdown
    if task := context.user_data.get("timer_task"):
        task.cancel()

    user_id = query.from_user.id
    index = context.user_data.get("question_index", 0)
    question = quiz_data[index]

    # Normalize both
    user_answer = normalize(query.data)
    correct_answer = normalize(question.get("answer", ""))

    elapsed = stop_timer(context.user_data["timer"])
    is_correct = (user_answer == correct_answer) and (elapsed <= question.get("time_limit", 30))

    # Record it
    update_player_answer(user_id, is_correct, elapsed)

    # Rebuild buttons with feedback
    new_markup = []
    for opt in question["options"]:
        norm_opt = normalize(opt)
        label = opt  # display label is the original
        if norm_opt == user_answer:
            # this is what they clicked
            label = ("✅ " if is_correct else "❌ ") + opt
        elif (norm_opt == correct_answer) and not is_correct:
            # they got it wrong so highlight the correct one
            label = "💡 " + opt
        new_markup.append([InlineKeyboardButton(label, callback_data="DISABLED")])

    try:
        await query.edit_message_reply_markup(InlineKeyboardMarkup(new_markup))
    except BadRequest:
        pass

    # Send updated rankings
    rankings = get_rankings(user_id)
    chat_id = update.effective_chat.id if update.effective_chat else context.user_data.get("chat_id")
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ Answer recorded!\n{rankings}"
    )

    # Move to next
    context.user_data["question_index"] = index + 1
    await asyncio.sleep(1)
    await send_question(update, context)


async def countdown_timer(context: ContextTypes.DEFAULT_TYPE, message, time_limit: int):
    user_data = context.user_data
    chat_id = user_data.get("chat_id")
    message_id = user_data.get("current_message_id")
    q = quiz_data[user_data["question_index"]]
    buttons = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in q["options"]]
    reply_markup = InlineKeyboardMarkup(buttons)

    for remaining in range(time_limit - 1, 0, -1):
        await asyncio.sleep(1)
        if user_data.get("answered"):
            return
        try:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"📖 *Q{user_data['question_index']+1}:* {q.get('text', '')}\n⏳ *{remaining} seconds*",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        except Exception:
            return

    if user_data.get("answered"):
        return

    locked_buttons = [[InlineKeyboardButton(f"⏳ {opt}", callback_data="DISABLED")] for opt in q["options"]]
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=InlineKeyboardMarkup(locked_buttons)
        )
    except Exception:
        pass

    update_player_answer(user_data["user_id"], False, time_limit)
    rankings = get_rankings(user_data["user_id"])
    await context.bot.send_message(chat_id=chat_id, text=f"⏱ Time's up!\n{rankings}")

    user_data["question_index"] += 1
    user_data["timer"] = start_timer()
    await send_question(message, context)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Start quiz\n"
        "/quizlist - Choose a quiz to play\n"
        "/createquiz - Create a new quiz\n"
        "/help - Show this message"
    )

async def replay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Reset user context and player stats for the quiz
    context.user_data["question_index"] = 0
    context.user_data["answered"] = False
    context.user_data["timer"] = start_timer()

    # Optionally reset player stats for this quiz
    # If you track per-quiz data, reset it here

    await update.message.reply_text("🔄 Quiz restarted! Good luck!")
    # Start the quiz from first question again
    await send_question(update, context)


from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

SELECT_QUIZ, SELECT_QUESTION, EDIT_ACTION, EDIT_TEXT = range(4)

async def editquiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("🛠️ /editquiz triggered")  # debug
    files = [f for f in os.listdir(QUIZ_DIR) if f.endswith(".json")]
    buttons = [[InlineKeyboardButton(f, callback_data=f"EDITQZ_{f}")] for f in files]
    await update.message.reply_text("Select quiz to edit:", reply_markup=InlineKeyboardMarkup(buttons))
    return SELECT_QUIZ

async def select_quiz_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    filename = query.data.replace("EDITQZ_", "")
    path = os.path.join(QUIZ_DIR, filename)
    with open(path, encoding="utf-8") as f:
        context.user_data["edit_quiz_data"] = json.load(f)
        context.user_data["edit_quiz_file"] = path

    buttons = [
        [InlineKeyboardButton(f"Q{i+1}: {q.get('text','')[:25]}...", callback_data=f"EDITQ_{i}")]
        for i, q in enumerate(context.user_data["edit_quiz_data"])
    ]
    await query.edit_message_text("Select question to edit:", reply_markup=InlineKeyboardMarkup(buttons))
    return SELECT_QUESTION

async def select_question_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    idx = int(query.data.replace("EDITQ_", ""))
    context.user_data["edit_index"] = idx

    buttons = [
        [InlineKeyboardButton("Edit Text", callback_data="EDIT_TEXT")],
        [InlineKeyboardButton("Delete Question", callback_data="DELETE")],
        [InlineKeyboardButton("Cancel", callback_data="CANCEL")],
    ]
    await query.edit_message_text("Choose action:", reply_markup=InlineKeyboardMarkup(buttons))
    return EDIT_ACTION

async def edit_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    action = query.data
    if action == "EDIT_TEXT":
        await query.edit_message_text("Send new text for this question:")
        return EDIT_TEXT
    elif action == "DELETE":
        data = context.user_data["edit_quiz_data"]
        idx = context.user_data["edit_index"]
        data.pop(idx)
        with open(context.user_data["edit_quiz_file"], "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        await query.edit_message_text("❌ Question deleted.")
        return ConversationHandler.END
    else:
        await query.edit_message_text("✋ Edit cancelled.")
        return ConversationHandler.END

async def edit_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    new_text = update.message.text
    idx = context.user_data["edit_index"]
    data = context.user_data["edit_quiz_data"]
    data[idx]["text"] = new_text
    with open(context.user_data["edit_quiz_file"], "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    await update.message.reply_text("✅ Question text updated.")
    return ConversationHandler.END

edit_quiz_handler = ConversationHandler(
    entry_points=[CommandHandler("editquiz", editquiz_command)],
    states={
        SELECT_QUIZ:   [CallbackQueryHandler(select_quiz_edit,   pattern="^EDITQZ_")],
        SELECT_QUESTION: [CallbackQueryHandler(select_question_edit, pattern="^EDITQ_")],
        EDIT_ACTION:  [CallbackQueryHandler(edit_action,        pattern="^(EDIT_TEXT|DELETE|CANCEL)$")],
        EDIT_TEXT:    [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_text)],
    },
    fallbacks=[]
)

# In‑memory store for active sessions
# { code: { host, participants:set, quiz:list, q_index:int, answers:dict(user_id→list) } }
multisessions = {}

def _new_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


async def handle_multi_answer(update, context):
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
    bot = context.bot
    for pid in sess["participants"]:
        msg_id = sess["message_ids"].get(pid)
        if msg_id:
            q_text = q.get("text", "")
            await bot.edit_message_text(
                chat_id=pid,
                message_id=msg_id,
                text=f"❓ Q{qidx+1}: {q_text}\n✅ Answered People: {count}"
            )

    if all(len(sess["answers"][pid]) == qidx + 1 for pid in sess["participants"]):
        sess["q_index"] += 1

        # ✅ Send live rankings to channel
        rankings = []
        for pid in sess["participants"]:
            p = sess["answers"][pid]
            pts = sum(a["score"] for a in p)
            correct = sum(1 for a in p if a["correct"])
            total = len(p)
            acc = int((correct / total) * 100) if total > 0 else 0
            t = int(sum(a["time"] for a in p))
            name = (await bot.get_chat(pid)).first_name
            rankings.append((pts, f"{name}: {pts} pts - {acc}% correct - {t}s"))

        rankings.sort(reverse=True)
        rank_text = "\n".join([r[1] for r in rankings])
        await bot.send_message(chat_id="@korai_verse", text=f"📢 Live Rankings After Q{qidx+1}:\n{rank_text}")

        await _broadcast_question(code)


from uuid import uuid4

import random

async def host_quiz(update, context):
    user = update.effective_user
    member = await update.effective_chat.get_member(user.id)
    if not member.status in ["creator", "administrator"]:
        await update.message.reply_text("❌ Only admins can host quizzes.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /hostquiz <quizname.json>")
        return

    filename = context.args[0]
    if not filename.endswith(".json"):
        filename += ".json"

    path = os.path.join("quizzes", filename)
    if not os.path.exists(path):
        await update.message.reply_text(f"❌ File `{filename}` not found.")
        return

    try:
        with open(path, encoding="utf-8") as f:
            quiz = json.load(f)
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to load quiz: {str(e)}")
        return

    while True:
        code = str(random.randint(100000, 999999))
        if code not in multisessions:
            break

    multisessions[code] = {
        "host": user.id,
        "quiz": quiz,
        "participants": [],
        "answers": {},
        "q_index": 0,
        "message_ids": {},
        "locked": False,
    }
    context.user_data["host_code"] = code

    await update.message.reply_text(f"✅ Quiz hosted with code: `{code}`\nAsk players to join with /join {code}")
    await context.bot.send_message(chat_id="@korai_verse", text=f"🌐 New quiz hosted!\nUse `/join {code}` to participate!\n🎮 Waiting for players...")

async def join_quiz(update, context):
    if not context.args:
        await update.message.reply_text("Usage: /join <code>")
        return

    code = context.args[0]
    if code not in multisessions:
        await update.message.reply_text("❌ Invalid code.")
        return

    sess = multisessions[code]
    if sess.get("locked"):
        await update.message.reply_text("⛔ This quiz has already started and is locked.")
        return

    user_id = update.effective_user.id
    if user_id not in sess["participants"]:
        sess["participants"].append(user_id)
        sess["answers"][user_id] = []

    names = [ (await context.bot.get_chat(pid)).first_name for pid in sess["participants"] ]
    await update.message.reply_text(f"✅ You joined session {code}\nWaiting for host to start...\n👥 Players:\n" + "\n".join(names))
    await context.bot.send_message(chat_id="@korai_verse", text=f"📢 {update.effective_user.first_name} joined quiz {code}\n👥 Players now: {len(sess['participants'])}")

async def start_hosted_quiz(update, context):
    code = context.user_data.get("host_code")
    if not code or code not in multisessions:
        await update.message.reply_text("❌ No hosted session found. Use /hostquiz first.")
        return

    sess = multisessions[code]
    sess["locked"] = True
    await update.message.reply_text("🚀 Starting the quiz now!")
    for pid in sess["participants"]:
        sess["answers"][pid] = []

    from player_manager import _broadcast_question
    await _broadcast_question(code)



# In quiz_handler.py

async def setquiz_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /setquiz <quizname.json>")
        return

    quizname = context.args[0]
    code = context.user_data.get("host_code")
    if not code or code not in multisessions:
        await update.message.reply_text("❌ You haven't started a hosted quiz yet. Use /hostquiz first.")
        return

    path = os.path.join("quizzes", quizname)
    if not os.path.exists(path):
        await update.message.reply_text("❌ Quiz not found.")
        return

    with open(path, encoding="utf-8") as f:
        quiz = json.load(f)

    multisessions[code]["quiz"] = quiz
    await update.message.reply_text(f"✅ Quiz `{quizname}` loaded for code {code}. You can now /startquiz.")


async def cancel_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code_to_cancel = None

    for code, sess in multisessions.items():
        if sess["host"] == user_id:
            code_to_cancel = code
            break

    if not code_to_cancel:
        await update.message.reply_text("❌ No hosted quiz session found.")
        return

    del multisessions[code_to_cancel]
    await update.message.reply_text(f"❌ Quiz session {code_to_cancel} cancelled.")


async def kick_user(update, context):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /kick <name>")
        return

    code = context.user_data.get("host_code")
    if not code or code not in multisessions:
        await update.message.reply_text("❌ No active session found.")
        return

    to_kick = context.args[0].lower()
    sess = multisessions[code]
    kicked = False
    bot = context.bot
    for pid in sess["participants"][:]:
        name = (await bot.get_chat(pid)).first_name.lower()
        if name == to_kick:
            sess["participants"].remove(pid)
            kicked = True
            await bot.send_message(pid, "🚫 You were removed from the session.")
    if kicked:
        await update.message.reply_text(f"✅ {to_kick} has been removed from session {code}.")
    else:
        await update.message.reply_text("❌ User not found in session.")

