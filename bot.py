# quiz_bot/bot.py
import os
import json
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from telegram.ext import ApplicationBuilder
from quiz_handler import (
    leaderboard_command,
    replay_command,
    editquiz_command,
    select_quiz_edit,
    select_question_edit,
    edit_action,
    edit_text,
    edit_quiz_handler,
    help_command,
    quizlist_command,
    select_quiz,
    handle_answer,
    send_question,
    get_rankings,
    host_quiz,
    start_hosted_quiz,
    handle_quizlist_buttons
)
import quiz_handler
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from quiz_creator import createquiz_command, handle_quiz_creation
from player_manager import add_player  # you need this
from utils import start_timer
from quiz_handler import send_question
from player_manager import start_session
from telegram import Update
from telegram.ext import CommandHandler, MessageHandler, filters, ConversationHandler, ContextTypes
# after your other imports
from telegram.ext import ConversationHandler
from quiz_processor import convert_file_to_quiz

# these must come after your imports:
WAITING_FILE, WAITING_QUIZ_NAME, WAITING_TIME = range(3)





# Constants and globals
QUIZ_DIR = "data/quizzes"
quiz_data = []
QUIZ_PATH = None

# Conversation state
NICKNAME = 1

# Start command - ask nickname
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Please enter your nickname to join the quiz.")
    return NICKNAME

async def instant_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📎 Please upload a .csv or .xlsx file with your quiz.")
    return WAITING_FILE


# Receive nickname
async def nickname_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nickname = update.message.text.strip()
    context.user_data["nickname"] = nickname
    await update.message.reply_text(f"Thanks, {nickname}! Now use /quizlist to select a quiz.")
    return ConversationHandler.END

# You can keep select_quiz inside quiz_handler or here,
# but if here, import all needed modules and globals accordingly.

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    rankings = get_rankings(user_id)
    await update.message.reply_text(f"🏆 Global Leaderboard:\n{rankings}")


async def instant_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Please send me the .csv or .xlsx file containing your quiz.")
    return WAITING_FILE

async def handle_file_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    if not document.file_name.endswith(('.csv', '.xlsx')):
        await update.message.reply_text("❌ Only .csv or .xlsx files are supported.")
        return ConversationHandler.END

    file = await document.get_file()
    file_path = f"/tmp/{document.file_name}"
    await file.download_to_drive(file_path)

    context.user_data["uploaded_file"] = file_path
    await update.message.reply_text("✏️ Please enter a name for your quiz file (without extension):")
    return WAITING_QUIZ_NAME

async def handle_quiz_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quiz_name = update.message.text.strip()
    # Sanitize quiz_name if needed
    context.user_data["quiz_name"] = quiz_name
    await update.message.reply_text("⏱️ Now enter the time limit for each question (in seconds):")
    return WAITING_TIME

async def handle_time_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        time_limit = int(update.message.text)
        file_path = context.user_data["uploaded_file"]
        quiz_name = context.user_data.get("quiz_name", "quiz")
        filename = convert_file_to_quiz(file_path, time_limit, quiz_name)
        await update.message.reply_text(f"✅ Quiz created and saved as `{filename}` in /data/quizzes.\nUse /quizlist to play it.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    return ConversationHandler.END


async def send_website_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Open the quiz editor:\nhttp://<YOUR_IP>:5000"
    )


# ---- end instant_quiz ----



if __name__ == "__main__":
    # BOT_TOKEN = os.getenv("BOT_TOKEN", "8197997289:AAFQKDDy4WpqXGJNl3UiZQGA7E-uTDnf_QU")
    BOT_TOKEN = "8197997289:AAFQKDDy4WpqXGJNl3UiZQGA7E-uTDnf_QU"
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # ✅ THEN assign to quiz_handler
    import quiz_handler
    quiz_handler.qh_app = app
    from quiz_handler import edit_quiz_handler
    quiz_handler.qh_app = app




    # Conversation handler for nickname
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_command)],
        states={
            NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, nickname_received)],
        },
        fallbacks=[],
    )

    app.add_handler(
    ConversationHandler(
        entry_points=[CommandHandler("instant_quiz", instant_quiz)],
        states={
            WAITING_FILE: [MessageHandler(filters.Document.ALL, handle_file_upload)],
            WAITING_QUIZ_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quiz_name)],
            WAITING_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_time_limit)],
        },
        fallbacks=[],
    )
)

    


    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("createquiz", createquiz_command))
    app.add_handler(CommandHandler("quizlist", quizlist_command))
    app.add_handler(CallbackQueryHandler(handle_quizlist_buttons, pattern="^(QUIZ|UP|DOWN|ENTER_REORDER|EXIT_REORDER)"))
    app.add_handler(CallbackQueryHandler(select_quiz, pattern="^QUIZ_"))
    app.add_handler(CallbackQueryHandler(handle_answer))
    app.add_handler(MessageHandler(filters.TEXT | filters.PHOTO, handle_quiz_creation))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("replay", replay_command))
    app.add_handler(edit_quiz_handler)  # ✅ This must be added after building the app
    
    from quiz_handler import (
    host_quiz, join_quiz, start_hosted_quiz, setquiz_command, cancel_quiz, kick_user, handle_multi_answer)

    app.add_handler(CommandHandler("hostquiz", host_quiz))
    app.add_handler(CommandHandler("join", join_quiz))
    app.add_handler(CommandHandler("startquiz", start_hosted_quiz))
    app.add_handler(CommandHandler("setquiz", setquiz_command))
    app.add_handler(CommandHandler("cancelquiz", cancel_quiz))
    app.add_handler(CommandHandler("kick", kick_user))
    app.add_handler(CommandHandler("website", send_website_link))
    app.add_handler(CallbackQueryHandler(handle_multi_answer, pattern=r"^MULTI\\|"))

    print("Bot is running...")
    app.run_polling()
   
   
