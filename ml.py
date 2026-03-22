import logging
import re
import json
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters
)
BOT_TOKEN = "7615544436:AAGhkg84m-nGyMxkqk072NGoUjtVwq8LFT0"
ADMIN_ID = 7533465237
ORDERS_FILE = "orders.json"
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
GAME_ID, PAYMENT_CONFIRMATION = range(2)
packages = {
    "Weekly Pass": 6100,
    "Twilight Pass": 33000,
    "86 Diamonds": 5100,
    "172 Diamonds": 10000,
    "257 Diamonds": 14400,
    "343 Diamonds": 19300,
}
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
else:
    orders = {}
def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    welcome_text = "👋 မင်္ဂလာပါ Customer ရေ!\nMLBB Diamonds ဝယ်ယူဖို့ ကြိုဆိုပါတယ်\n💎 Package ကို အောက်မှာရွေးချယ်နိုင်ပါတယ်။"
    keyboard = []
    row = []
    for idx, (name, price) in enumerate(packages.items(), 1):
        row.append(InlineKeyboardButton(f"{name} - {price} MMK", callback_data=name))
        if idx % 2 == 0:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return GAME_ID
async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    package_name = query.data
    context.user_data["package"] = package_name
    uid = str(update.effective_user.id)
    orders[uid] = {"package": package_name, "status": "pending"}
    save_orders()
    await query.edit_message_text(f"✅ သင်ရွေးချယ်ထားတာ: {package_name}\nကျေးဇူးပြုပြီး သင့် Game ID နှင့် Server ID ပေးပို့ပါ")
    return PAYMENT_CONFIRMATION
def validate_game_id(game_id_text: str) -> bool:
    pattern = r"^\d{5,10}( \(\d{1,5}\))?$"
    return re.match(pattern, game_id_text) is not None
async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    if not validate_game_id(text):
        await update.message.reply_text("❌ Game ID format မမှန်ပါ။ 12345678 (9012) အတိုင်းပေးပါ။")
        return PAYMENT_CONFIRMATION
    uid = str(update.effective_user.id)
    context.user_data["game_id"] = text
    orders[uid]["game_id"] = text
    save_orders()
    package = context.user_data["package"]
    amount = packages[package]
    await update.message.reply_text(f"💳 ငွေပေးချေရန်\nWavePay Number: 09758486680\nAmount: {amount} MMK\nငွေလွှဲပြီး Screenshot ပေးပို့ပါ။")
    return PAYMENT_CONFIRMATION
async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = str(update.effective_user.id)
    if uid not in orders:
        await update.message.reply_text("Error! /start နဲ့ ပြန်စပါ")
        return ConversationHandler.END
    orders[uid]["proof"] = update.message.photo[-1].file_id if update.message.photo else update.message.text
    save_orders()
    await update.message.reply_text("📌 သင့် order ကို Admin ဆီပိုပို့ပြီးပါပြီ။")
    return ConversationHandler.END
async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    decision, target_user = query.data.split("_")
    uid = str(target_user)
    if uid not in orders:
        await query.edit_message_text("Order not found ❌")
        return
    if decision == "accept":
        await context.bot.send_message(chat_id=target_user, text="✅ Order accepted!")
        orders[uid]["status"] = "accepted"
    else:
        await context.bot.send_message(chat_id=target_user, text="❌ Order rejected!")
        orders[uid]["status"] = "rejected"
    save_orders()
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Order cancelled. /start နဲ့ ပြန်စပါ")
    return ConversationHandler.END
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            GAME_ID: [CallbackQueryHandler(select_package)],
            PAYMENT_CONFIRMATION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_game_id),
                MessageHandler(filters.PHOTO, receive_payment_proof)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(admin_decision, pattern="^(accept|reject)_"))
    app.run_polling()
if __name__ == "__main__":
    main()
