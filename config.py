from telegram.ext import ApplicationBuilder
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8197997289:AAFQKDDy4WpqXGJNl3UiZQGA7E-uTDnf_QU")

application = ApplicationBuilder().token(BOT_TOKEN).build()
