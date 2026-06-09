"""
ELBorsaa Halal Bot - بوت البورصة الحلال المصرية
Telegram bot connected to Claude AI for Egyptian halal stock market analysis
Requirements: pip install python-telegram-bot anthropic
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
import anthropic

# ============================================================
# الإعدادات - ضع مفاتيحك هنا
# ============================================================
TELEGRAM_TOKEN  = 8990067768:AAEPARFzwvexiQRo21GHbV2w87rTxA-pn2w
ANTHROPIC_API_KEY = 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
# ============================================================
# إعداد السجل
# ============================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============================================================
# إعداد عميل أنثروبيك
# ============================================================
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ============================================================
# الأسهم المحرمة في البورصة المصرية (قائمة مرجعية)
# ============================================================
HARAM_STOCKS = {
    "EAST": "الشرقية للدخان - قطاع التبغ محرم شرعاً",
    "SPMD": "سبيدي - نشاط مشكوك فيه",
}

HARAM_SECTORS = [
    "التبغ والسجائر",
    "البنوك التقليدية الربوية",
    "شركات التأمين التقليدي",
    "الكحول والمشروبات الكحولية",
]

# أسهم حلال بارزة في EGX للإرشاد
HALAL_STARS = [
    ("HRHO", "مجموعة هيرميس المالية القابضة"),
    ("OCDI", "أوراسكوم للتنمية"),
    ("PHDC", "بالم هيلز للتعمير"),
    ("MNHD", "مدينة نصر للإسكان"),
    ("ORTE", "أوراسكوم للإنشاء"),
    ("SWDY", "السويدي إلكتريك"),
    ("CLHO", "كليوباترا للمستشفيات"),
    ("EGAL", "مصر للغازات"),
]

# ============================================================
# System Prompt متخصص في البورصة المصرية
# ============================================================
SYSTEM_PROMPT = """أنت محلل مالي إسلامي متخصص حصرياً في البورصة المصرية (EGX).

🏛️ **تخصصك الكامل:**
- البورصة المصرية (Egyptian Exchange - EGX)
- مؤشر EGX 30 (الأسهم القيادية)
- مؤشر EGX 70 (الأسهم الصغيرة والمتوسطة)
- مؤشر EGX 100
- مؤشر الشريعة الإسلامية EGX (المؤشر الشرعي الرسمي للبورصة المصرية)

━━━━━━━━━━━━━━━━━━━━━━
📋 **منهجية التحليل الشرعي:**
━━━━━━━━━━━━━━━━━━━━━━

أولاً: الفلترة الشرعية الفورية
• ⛔ محرم قطعاً: التبغ (الشرقية للدخان EAST)، الكحول، القمار
• ⛔ محرم: البنوك الربوية (CIB، QNB مصر، بنك مصر التقليدي...) ما لم تكن لديها نافذة إسلامية معتمدة
• ⚠️ مشكوك فيه: شركات التأمين التقليدي — تحتاج فحصاً للنسب
• ✅ مرشح للحلال: شركات الاتصالات، العقارات، الصناعة، الرعاية الصحية، الطاقة، التكنولوجيا

ثانياً: معايير نسب الحلال (AAOIFI)
• نسبة الديون الربوية < 33% من إجمالي الأصول
• نسبة الإيرادات المحرمة < 5% من إجمالي الإيرادات
• السيولة النقدية وحسابات البنوك الربوية < 33% من القيمة السوقية

ثالثاً: مؤشر الشريعة المصري
• البورصة المصرية لديها مؤشر شريعة رسمي — استخدمه كمرجع أول
• الأسهم المدرجة في مؤشر الشريعة EGX هي الأكثر موثوقية

━━━━━━━━━━━━━━━━━━━━━━
📊 **التحليل الفني والأساسي:**
━━━━━━━━━━━━━━━━━━━━━━
• مستويات الدعم والمقاومة بالجنيه المصري
• الاتجاه: صاعد 📈 / هابط 📉 / عرضي ↔️
• مؤشرات: RSI، المتوسطات المتحركة MA20 وMA50
• مضاعف الربحية P/E مقارنة بالقطاع المصري
• العائد على حقوق الملكية ROE
• القيمة السوقية بالمليار جنيه
• أداء السهم منذ بداية العام YTD%

━━━━━━━━━━━━━━━━━━━━━━
🎯 **شكل التوصية الإلزامي:**
━━━━━━━━━━━━━━━━━━━━━━

🟢 **شراء** — مع سعر دخول مقترح وهدف ووقف خسارة
🔴 **بيع** — مع سبب واضح
🟡 **انتظار** — مع شرط الدخول
⛔ **محرم** — مع تفصيل السبب الشرعي
⚠️ **مشكوك فيه** — مع نصيحة الابتعاد احتياطاً

━━━━━━━━━━━━━━━━━━━━━━
💡 **تنسيق الرد:**
━━━━━━━━━━━━━━━━━━━━━━
1. اسم الشركة + رمز التداول
2. القطاع
3. الحكم الشرعي (مع السبب)
4. التحليل المختصر (4-5 نقاط)
5. التوصية + أسعار الدخول/الهدف/الوقف
6. تنبيه إلزامي: "⚠️ للاستئناس فقط، ليس نصيحة استثمارية"

تحدث بالعربية دائماً. كن دقيقاً ومختصراً."""

# ============================================================
# دوال التحليل
# ============================================================
async def analyze_stock(query: str) -> str:
    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1500,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"حلل لي هذا السهم في البورصة المصرية وأعطني توصية: {query}"}]
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"خطأ Claude: {e}")
        return "❌ حدث خطأ في التحليل. يرجى المحاولة لاحقاً."


async def analyze_with_query(query: str) -> str:
    try:
        message = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=1400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": query}]
        )
        return message.content[0].text
    except Exception as e:
        logger.error(f"خطأ: {e}")
        return "❌ حدث خطأ. يرجى المحاولة لاحقاً."

# ============================================================
# أوامر التيليجرام
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("📊 نظرة السوق", callback_data="market"),
         InlineKeyboardButton("✅ أسهم حلال مقترحة", callback_data="halal_list")],
        [InlineKeyboardButton("⛔ الأسهم المحرمة", callback_data="haram_list"),
         InlineKeyboardButton("📖 كيف أستخدم البوت؟", callback_data="howto")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "🌙 *أهلاً بك في ELBorsaa Halal Bot*\n"
        "محللك الذكي للبورصة المصرية وفق أحكام الشريعة\n\n"
        "📩 *أرسل لي مباشرة:*\n"
        "• اسم الشركة: `أوراسكوم` أو `بالم هيلز`\n"
        "• رمز التداول: `OCDI` أو `PHDC`\n"
        "• سؤالاً مفتوحاً: _هل CIB حلال؟_\n\n"
        "أو اختر من القائمة:"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📖 *دليل الاستخدام*\n\n"
        "*الأوامر:*\n"
        "/start — الصفحة الرئيسية\n"
        "/market — حالة السوق الآن\n"
        "/halal — قائمة أسهم حلال مقترحة\n"
        "/haram — الأسهم المحرمة المعروفة\n"
        "/sharia — عن مؤشر الشريعة EGX\n\n"
        "*أمثلة:*\n"
        "• `حلل سهم السويدي`\n"
        "• `هل موبي للتمويل حلال؟`\n"
        "• `SWDY توصية`\n"
        "• `أفضل 3 أسهم عقارية حلال`\n\n"
        "*معايير الحلال (AAOIFI):*\n"
        "✅ ديون ربوية < 33%\n"
        "✅ إيرادات محرمة < 5%\n"
        "✅ القطاع مباح شرعاً\n"
        "✅ مدرج في مؤشر الشريعة EGX"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = await update.message.reply_text("📊 جاري تحليل البورصة المصرية...")
    query = (
        "أعطني نظرة عامة على البورصة المصرية الآن:\n"
        "1. حالة مؤشر EGX 30 واتجاهه\n"
        "2. حالة مؤشر الشريعة EGX\n"
        "3. أبرز القطاعات الواعدة شرعياً وفنياً\n"
        "4. 3 أسهم حلال تستحق المتابعة هذه الفترة مع أسباب\n"
        "5. أبرز المخاطر الحالية للسوق المصري"
    )
    response = await analyze_with_query(query)
    await msg.delete()
    await update.message.reply_text(response, parse_mode="Markdown")


async def halal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    stars = "\n".join([f"• `{code}` — {name}" for code, name in HALAL_STARS])
    text = (
        "✅ *أسهم مرشحة للحلال في EGX*\n"
        "_(بناءً على مؤشر الشريعة EGX وتحليل القطاع)_\n\n"
        f"{stars}\n\n"
        "📌 أرسل رمز أي سهم لتحليل مفصّل وتوصية\n"
        "⚠️ راجع دائماً أحدث تقارير الشريعة قبل الاستثمار"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def haram_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    haram_list = "\n".join([f"⛔ `{code}` — {reason}" for code, reason in HARAM_STOCKS.items()])
    sectors = "\n".join([f"🚫 {s}" for s in HARAM_SECTORS])
    text = (
        "⛔ *الأسهم والقطاعات المحرمة في EGX*\n\n"
        "*أسهم محرمة معروفة:*\n"
        f"{haram_list}\n\n"
        "*قطاعات محرمة أو مشكوك فيها:*\n"
        f"{sectors}\n\n"
        "💡 _للاستفسار عن أي سهم آخر أرسل اسمه مباشرة_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def sharia_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "🕌 *مؤشر الشريعة الإسلامية — EGX*\n\n"
        "البورصة المصرية أطلقت مؤشراً شرعياً رسمياً يضم الأسهم "
        "المتوافقة مع أحكام الشريعة الإسلامية.\n\n"
        "*معايير الإدراج في المؤشر:*\n"
        "• القطاع مباح شرعاً\n"
        "• نسبة الديون الربوية < 33% من الأصول\n"
        "• نسبة الإيرادات المحرمة < 5%\n"
        "• يُراجَع ويُحدَّث دورياً\n\n"
        "*كيف تتحقق؟*\n"
        "الموقع الرسمي: egx.com.eg\n"
        "ابحث عن: مؤشر الشريعة الإسلامية\n\n"
        "أرسل اسم أي سهم وسأخبرك إن كان ضمن المؤشر أم لا 👇"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ============================================================
# معالج أزرار الكيبورد
# ============================================================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "market":
        await query.message.reply_text("📊 جاري التحليل...")
        q = (
            "نظرة عامة على البورصة المصرية الآن:\n"
            "1. حالة EGX30 واتجاهه\n"
            "2. حالة مؤشر الشريعة EGX\n"
            "3. أبرز 3 أسهم حلال واعدة مع أسباب\n"
            "4. أبرز مخاطر السوق"
        )
        resp = await analyze_with_query(q)
        await query.message.reply_text(resp, parse_mode="Markdown")

    elif data == "halal_list":
        stars = "\n".join([f"• `{c}` — {n}" for c, n in HALAL_STARS])
        await query.message.reply_text(
            f"✅ *أسهم مرشحة للحلال في EGX:*\n\n{stars}\n\n"
            "أرسل رمز أي سهم لتحليل مفصّل 👇",
            parse_mode="Markdown"
        )

    elif data == "haram_list":
        haram = "\n".join([f"⛔ `{c}` — {r}" for c, r in HARAM_STOCKS.items()])
        sectors = "\n".join([f"🚫 {s}" for s in HARAM_SECTORS])
        await query.message.reply_text(
            f"⛔ *الأسهم المحرمة:*\n{haram}\n\n*القطاعات المحرمة:*\n{sectors}",
            parse_mode="Markdown"
        )

    elif data == "howto":
        await query.message.reply_text(
            "📖 *طريقة الاستخدام:*\n\n"
            "فقط اكتب اسم السهم أو رمزه مثل:\n"
            "• `SWDY` أو `السويدي إلكتريك`\n"
            "• `هل أوراسكوم حلال؟`\n"
            "• `أفضل أسهم عقارية حلال`\n\n"
            "وسأرد بتحليل شرعي + فني + توصية فورية ✅",
            parse_mode="Markdown"
        )


# ============================================================
# معالج الرسائل النصية
# ============================================================
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    user_name = update.message.from_user.first_name or "صديقي"

    logger.info(f"رسالة من {user_name}: {user_message}")

    thinking_msg = await update.message.reply_text(
        f"🔍 جاري تحليل *{user_message}* في البورصة المصرية...",
        parse_mode="Markdown"
    )

    analysis = await analyze_stock(user_message)
    await thinking_msg.delete()
    await update.message.reply_text(analysis, parse_mode="Markdown")


# ============================================================
# نقطة الدخول
# ============================================================
def main() -> None:
    print("🚀 جاري تشغيل ELBorsaa Halal Bot (البورصة المصرية)...")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("help",    help_command))
    app.add_handler(CommandHandler("market",  market_command))
    app.add_handler(CommandHandler("halal",   halal_command))
    app.add_handler(CommandHandler("haram",   haram_command))
    app.add_handler(CommandHandler("sharia",  sharia_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("✅ البوت يعمل! اضغط Ctrl+C للإيقاف")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

