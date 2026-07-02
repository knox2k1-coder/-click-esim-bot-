import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Conversation States
CHOOSING_OPERATOR, CHOOSING_QUANTITY, ENTERING_CONTACT, SENDING_RECEIPT = range(4)

# Fixed Price
ESIM_PRICE = 15000

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = (
        "မင်္ဂလာပါဗျာ 🙏 *Click eSIM* မှ ကြိုဆိုပါတယ်။\n\n"
        "အပြင်ပေါက်ဈေးထက် ပိုမိုသက်သာတဲ့ အော်ပရေတာစုံ eSIM QR များကို "
        f"တစ်ကတ်လျှင် *{ESIM_PRICE:,} ကျပ်တည်း* ဖြင့် Click တစ်ချက်နှိပ်ရုံနဲ့ အလွယ်တကူ ဝယ်ယူနိုင်ပါပြီ။"
    )
    keyboard = [
        [InlineKeyboardButton("🛒 eSIM QR ဝယ်ယူရန်", callback_data="buy_esim")],
        [InlineKeyboardButton("📖 eSIM ထည့်သွင်းနည်းလမ်းညွှန်", callback_data="guide")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
        
    return CHOOSING_OPERATOR

# Operator Selection
async def choose_operator(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "guide":
        keyboard = [[InlineKeyboardButton("🔙 မီနူးအစသို့ ပြန်သွားရန်", callback_data="back_to_start")]]
        await query.edit_message_text(
            "📖 *eSIM ထည့်သွင်းနည်းလမ်းညွှန်*\n\n"
            "၁။ ဖုန်း Setting -> Cellular/Mobile Data သို့သွားပါ။\n"
            "၂။ Add eSIM သို့မဟုတ် Add Data Plan ကိုနှိပ်ပါ။\n"
            "၃။ ကျွန်ုပ်တို့ပေးပို့သော QR Code ကို Scan ဖတ်ပြီး Activate လုပ်ပါ။",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return CHOOSING_OPERATOR

    keyboard = [
        [InlineKeyboardButton("🟡 ATOM eSIM", callback_data="op_ATOM")],
        [InlineKeyboardButton("🔴 Ooredoo eSIM", callback_data="op_Ooredoo")],
        [InlineKeyboardButton("🔵 MPT eSIM", callback_data="op_MPT")],
        [InlineKeyboardButton("🟢 Mytel eSIM", callback_data="op_Mytel")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="back_to_start")]
    ]
    await query.edit_message_text("👇 လူကြီးမင်း ဝယ်ယူလိုသော အော်ပရေတာ eSIM ကို ရွေးချယ်ပေးပါ ခင်ဗျာ။", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_QUANTITY

# Quantity Selection
async def choose_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_start":
        return await start(update, context)
        
    # Save selected operator to user_data
    context.user_data['operator'] = query.data.split('_')[1]
    
    keyboard = [
        [InlineKeyboardButton("၁ ကတ်", callback_data="qty_1"), InlineKeyboardButton("၂ ကတ်", callback_data="qty_2")],
        [InlineKeyboardButton("၃ ကတ်", callback_data="qty_3"), InlineKeyboardButton("၄ ကတ်", callback_data="qty_4")],
        [InlineKeyboardButton("🔙 နောက်သို့", callback_data="back_to_operator")]
    ]
    await query.edit_message_text(
        f"Selected: *{context.user_data['operator']} eSIM*\n\n"
        "🔢 ဘယ်နှစ်ကတ် ဝယ်ယူလိုပါသလဲခင်ဗျာ။ အောက်ပါခလုတ်များမှ ရွေးချယ်ပေးပါ။", 
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ENTERING_CONTACT

# Contact Entry Request
async def request_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "back_to_operator":
        return await choose_operator(update, context)
        
    qty = int(query.data.split('_')[1])
    context.user_data['quantity'] = qty
    total_price = qty * ESIM_PRICE
    context.user_data['total_price'] = total_price
    
    await query.edit_message_text(
        f"📝 *Order Summary*\n"
        f"• အော်ပရေတာ: {context.user_data['operator']}\n"
        f"• အရေအတွက်: {qty} ကတ်\n"
        f"• စုစုပေါင်းကျသင့်ငွေ: *{total_price:,} ကျပ်*\n\n"
        "📨 eSIM QR Code ပုံများ ပေးပို့ပေးနိုင်ရန် လူကြီးမင်း လက်ရှိအသုံးပြုနေသော "
        "*Viber ဖုန်းနံပါတ် သို့မဟုတ် Email Address* ကို အောက်တွင် ရိုက်ထည့်ပေးပါရန်။"
    )
    return SENDING_RECEIPT

# Payment & Receipt Request
async def request_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    contact_info = update.message.text
    context.user_data['contact'] = contact_info
    
    payment_text = (
        f"💰 *ငွေပေးချေရန်*\n\n"
        f"စုစုပေါင်းကျသင့်ငွေ *{context.user_data['total_price']:,} ကျပ်* ကို အောက်ပါ အကောင့်သို့ လွှဲပေးပါရန်။\n\n"
        f"📱 *KPay / Wave:* 09xxxxxxxxx\n"
        f"👤 *Account Name:* U Kyaw Kyaw\n\n"
        f"⚠️ ငွေလွှဲပြီးပါက *ငွေလွှဲပြေစာ Screenshot (Receipt)* ကို ဤနေရာသို့ ပို့ပေးပါရန်။ Admin မှ စစ်ဆေးပြီး eSIM QR ချက်ချင်း ပို့ပေးပါမည်။"
    )
    await update.message.reply_text(payment_text, parse_mode="Markdown")
    return ConversationHandler.END # End conversation flow, next is handling image receipt

# Handle Screenshot Receipt
async def handle_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        # Here you can route the photo to Admin Group or Database
        user = update.message.from_user
        await update.message.reply_text("✅ လူကြီးမင်း ပေးပို့သော ပြေစာကို လက်ခံရရှိပါပြီဗျာ။ Admin မှ စစ်ဆေးပြီး ခဏအတွင်း eSIM QR Code ပို့ပေးပါမည်။ ကျေးဇူးတင်ပါတယ်!")
        
        # Log or Send to Admin (Pseudo-code)
        # await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"New Order from {user.username}...")
    else:
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ ငွေလွှဲပြေစာ Screenshot (ဓာတ်ပုံ) ကို ပို့ပေးပါရန်။")

def main():
    # Replace with your actual Bot Token from BotFather
    TOKEN = "YOUR_BOT_TOKEN_HERE" 
    
    app = Application.builder().token(TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(start, pattern="^back_to_start$")],
        states={
            CHOOSING_OPERATOR: [CallbackQueryHandler(choose_operator)],
            CHOOSING_QUANTITY: [CallbackQueryHandler(choose_quantity)],
            ENTERING_CONTACT: [CallbackQueryHandler(request_contact)],
            SENDING_RECEIPT: [MessageHandler(filters.TEXT & ~filters.COMMAND, request_payment)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.PHOTO, handle_receipt))
    
    print("Click eSIM Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
