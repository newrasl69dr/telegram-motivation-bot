import json
import datetime
import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# Загружаем токен и ID из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
USER_ID = int(os.getenv("USER_ID"))

if not TOKEN or not USER_ID:
    raise ValueError("Переменные среды BOT_TOKEN и USER_ID должны быть заданы!")

DATA_FILE = "data.json"

MOTIVATIONS = [
    "Ты сильнее, чем кажется.",
    "Каждый день — новый шанс стать лучше.",
    "Ты не один в этом пути.",
    "Сегодня — идеальный день не сдаваться.",
    "Ты управляешь своей жизнью.",
    "Срыв — это не поражение, а урок.",
    # ... добавь остальные мотивации при желании
]

def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"start_date": None, "days": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_day_number(start_date):
    today = datetime.date.today()
    delta = today - datetime.date.fromisoformat(start_date)
    return delta.days + 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return
    data = load_data()
    if not data["start_date"]:
        data["start_date"] = str(datetime.date.today())
        save_data(data)
        await update.message.reply_text("📅 Отсчёт начат с сегодняшнего дня.")
    else:
        await update.message.reply_text("📅 Отсчёт уже начат.")

async def handle_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return
    text = update.message.text
    today = str(datetime.date.today())
    data = load_data()
    data["days"].append({"date": today, "response": text})
    save_data(data)
    await update.message.reply_text("✅ Ответ сохранён.")

async def send_motivation(context: ContextTypes.DEFAULT_TYPE):
    message = random.choice(MOTIVATIONS)
    await context.bot.send_message(chat_id=USER_ID, text=f"💪 {message}")

async def send_stat_request(context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data["start_date"]:
        return
    day_number = get_day_number(data["start_date"])
    text = f"""📅 День: {day_number}
🧠 Срыв: (да/нет)
🛏 Сон до 23:30: (да/нет)"""
    await context.bot.send_message(chat_id=USER_ID, text=text)

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != USER_ID:
        return
    data = load_data()
    total = len(data["days"])
    no_fails = sum(1 for d in data["days"] if "нет" in d["response"].lower())
    week_data = [d for d in data["days"] if datetime.date.fromisoformat(d["date"]) >= datetime.date.today() - datetime.timedelta(days=7)]
    month_data = [d for d in data["days"] if datetime.date.fromisoformat(d["date"]).month == datetime.date.today().month]

    await update.message.reply_text(
        f"📊 Всего дней: {total}\n"
        f"✅ Без срывов: {no_fails}\n"
        f"📆 За неделю: {len(week_data)}\n"
        f"📅 За месяц: {len(month_data)}"
    )

async def main():
    app = Application.builder().token(TOKEN).build()

    # Планировщик запускается внутри события
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send_motivation, "cron", hour=19, minute=0, args=[app])
    scheduler.add_job(send_stat_request, "cron", hour=23, minute=30, args=[app])
    scheduler.start()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_response))

    print("Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
