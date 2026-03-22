import logging
import re
import json
import os
import asyncio
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

# --- CONFIG ---
BOT_TOKEN = "7615544436:AAGhkg84m-nGyMxkqk072NGoUjtVwq8LFT0"
ADMIN_ID = 7533465237
ORDERS_FILE = "orders.json"

# --- Logging ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Conversation States ---
GAME_ID, PAYMENT_CONFIRMATION = range(2)

# --- Packages ---
packages = {
    "Weekly Pass": 6100,
    "Twilight Pass": 33000,
    "86 Diamonds": 5100,
    "172 Diamonds": 10000,
    "257 Diamonds": 14400,
    "343 Diamonds": 19300,
    "429 Diamonds": 23900,
    "514 Diamonds": 28600,
    "600 Diamonds": 33500,
    "706 Diamonds": 38400,
    "792 Diamonds": 43300,
    "878 Diamonds": 47900,
    "963 Diamonds": 52800,
    "1049 Diamonds": 57400,
    "1135 Diamonds": 63300,
    "1220 Diamonds": 67300,
    "1412 Diamonds": 77500,
    "2195 Diamonds": 118500,
    "2901 Diamonds": 155500,
    "3688 Diamonds": 195000,
    "5532 Diamonds": 292500,
    "6238 Diamonds": 330000,
    "7366 Diamonds": 386000,
    "9288 Diamonds": 492000,
}

# --- Orders storage (persist) ---
if os.path.exists(ORDERS_FILE):
    with open(ORDERS_FILE, "r") as f:
        orders = json.load(f)
else:
    orders = {}

def save_orders():
    with open(ORDERS_FILE, "w") as f:
        json.dump(orders, f, indent=2)

# --- START COMMAND ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    welcome_text = (
        "👋 မင်္ဂလာပါ Customer ရေ!\n\n"
        "MLBB Diamonds ဝယ်ယူဖို့ ကြိုဆိုပါတယ်ဗျ\n\n"
        "💎 Package ကို အောက်မှာရွေးချယ်နိုင်ပါတယ်။\n"
        "အားပေးမှုအတွက် ကျေးဇူးတင်ပါတယ်ဗျ 🙏\n"
        "ကောင်းသောနေ့လေး ပိုင်ဆိုင်နိုင်ပါစေ 🌸"
    )
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

# --- Package Selection ---
async def select_package(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    package_name = query.data
    context.user_data["package"] = package_name
    uid = str(update.effective_user.id)
    orders[uid] = {"package": package_name, "status": "pending"}
    save_orders()

    await query.edit_message_text(
        f"✅ သင်ရွေးချယ်ထားတာ: {package_name}\n\n"
        "ကျေးဇူးပြုပြီး သင့် Game ID နှင့် Server ID (Zone ID) ကို ပေးပို့ပါ\n"
        "ဥပမာ 👉 12345678 (9012)"
    )
    return PAYMENT_CONFIRMATION

# --- Validate Game ID ---
def validate_game_id(game_id_text: str) -> bool:
    pattern = r"^\d{5,10}( \(\d{1,5}\))?$"
    return re.match(pattern, game_id_text) is not None

# --- Receive Game ID ---
async def receive_game_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    game_id_full = update.message.text.strip()
    if not validate_game_id(game_id_full):
        await update.message.reply_text(
            "❌ Game ID format မမှန်ပါ။ ဥပမာ 12345678 (9012) အတိုင်းပေးပို့ပါ။"
        )
        return PAYMENT_CONFIRMATION

    context.user_data["game_id"] = game_id_full
    uid = str(update.effective_user.id)
    orders[uid]["game_id"] = game_id_full
    save_orders()

    package = context.user_data["package"]
    amount = packages[package]

    await update.message.reply_text(
        f"💳 ငွေပေးချေရန်\n\n"
        f"📱 WavePay Number: 09758486680\n"
        f"💸 Amount: {amount} MMK\n\n"
        "ငွေလွှဲပြီး Screenshot (သို့) Transaction ID ပေးပို့ပါ။"
    )
    return PAYMENT_CONFIRMATION

# --- Receive Payment Proof ---
async def receive_payment_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    uid = str(update.effective_user.id)
    if uid not in orders or "game_id" not in context.user_data:
        await update.message.reply_text("Error! /start နဲ့ ပြန်စပါဗျ")
        return ConversationHandler.END

    orders[uid]["proof"] = update.message.photo[-1].file_id if update.message.photo else update.message.text
    save_orders()

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Accept", callback_data=f"accept_{uid}")],
        [InlineKeyboardButton("❌ Reject", callback_data=f"reject_{uid}")]
    ])

    package = context.user_data["package"]
    game_id = context.user_data["game_id"]

    order_text = (
        f"🆕 New Order!\n\n"
        f"👤 User: {uid}\n"
        f"🎁 Package: {package}\n"
        f"🆔 Game ID: {game_id}\n\n"
        "📌 Proof အောက်ပါ message ထဲပါ"
    )

    if update.message.photo:
        await context.bot.send_photo(chat_id=ADMIN_ID,
                                     photo=update.message.photo[-1].file_id,
                                     caption=order_text,
                                     reply_markup=buttons)
    else:
        await context.bot.send_message(chat_id=ADMIN_ID, text=order_text, reply_markup=buttons)

    await update.message.reply_text("📌 သင့် order ကို Admin ဆီပိုပို့ပြီးပါပြီ။ ခဏစောင့်ပေးပါ။")
    return ConversationHandler.END

# --- Admin Decision ---
async def admin_decision(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    decision, target_user = query.data.split("_")
    uid = str(target_user)

    if uid not in orders:
        await query.edit_message_text("Order not found ❌")
        return

    if decision == "accept":
        await context.bot.send_message(chat_id=target_user, text="✅ သင့် Order အတည်ပြုပြီး Diamonds ဖြည့်မည်!")
        await query.edit_message_text("Order Accepted ✅")
        orders[uid]["status"] = "accepted"
    else:
        await context.bot.send_message(chat_id=target_user,
                                       text="❌ သင့် Order ကို ငြင်းပယ်လိုက်ပါပြီ။ /start ဖြင့် ပြန်စနိုင်သည်။")
        await query.edit_message_text("Order Rejected ❌")
        orders[uid]["status"] = "rejected"
    save_orders()

# --- Cancel ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Order ကို ဖျက်လိုက်ပါပြီ။ /start နဲ့ ပြန်စပါဗျ")
    return ConversationHandler.END

# --- Admin Commands ---
async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    pending = [f"User: {uid}, Package: {v['package']}, Status: {v['status']}" 
               for uid, v in orders.items() if v.get("status") == "pending"]
    text = "\n".join(pending) if pending else "No pending orders."
    await update.message.reply_text(text)

async def cmd_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /user <user_id>")
        return
    try:
        uid = str(int(context.args[0]))
        order = orders.get(uid)
        if not order:
            await update.message.reply_text("User not found.")
            return
        text = f"User: {uid}\nPackage: {order['package']}\nGame ID: {order.get('game_id','N/A')}\nStatus: {order.get('status','pending')}"
        await update.message.reply_text(text)
    except ValueError:
        await update.message.reply_text("User ID must be a number.")

async def cmd_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    msg = " ".join(context.args)
    success = 0
    for uid in orders.keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=msg)
            success += 1
        except:
            continue
    await update.message.reply_text(f"Broadcast sent to {success} users.")

# --- Main ---
async def main():
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
    app.add_handler(CommandHandler("pending", cmd_pending))
    app.add_handler(CommandHandler("user", cmd_user))
    app.add_handler(CommandHandler("broadcast", cmd_broadcast))

    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
