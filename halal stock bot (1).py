"""
🌙 ELBorsaa Halal Bot - البورصة المصرية
@ELBorsaa_halal_bot — Halal Stock Screening Bot for EGX via Telegram
"""

import os
import logging
import anthropic
import yfinance as yf
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

# ─── إعداد اللوق ──────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── التوكنات (من متغيرات البيئة) ────────────────────────────────
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─── قاموس الأسهم المصرية (رمز Yahoo Finance → اسم عربي) ──────────
EGX_STOCKS = {
    "COMI.CA":  "البنك التجاري الدولي",
    "HRHO.CA":  "هيرميس القابضة",
    "TMGH.CA":  "طلعت مصطفى القابضة",
    "MNHD.CA":  "مدينة نصر للإسكان",
    "SWDY.CA":  "السويدي إليكتريك",
    "EGTS.CA":  "المصرية للاتصالات (اتصالات مصر)",
    "CLHO.CA":  "سيلاه للرعاية الصحية",
    "JUFO.CA":  "جهينة للصناعات الغذائية",
    "ORWE.CA":  "عمر أفندي",
    "EFIH.CA":  "EFG هيرميس القابضة",
    "PHDC.CA":  "فاليو لخدمات المدفوعات",
    "AMOC.CA":  "الإسكندرية لتكرير البترول",
    "SKPC.CA":  "سيد كير للبلاستيك",
    "ALCN.CA":  "الكابلات المصرية",
}

HARAM_SECTORS = ["Banks", "Financial Services", "Consumer Defensive—Beverages—Alcoholic"]
WARNING_SECTORS = ["Financial Services", "Insurance"]

# ─── دالة جلب بيانات السهم ────────────────────────────────────────
def get_stock_data(ticker: str) -> dict | None:
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if not info or info.get("regularMarketPrice") is None:
            return None

        total_debt    = info.get("totalDebt", 0) or 0
        total_assets  = info.get("totalAssets", 1) or 1
        total_revenue = info.get("totalRevenue", 1) or 1
        interest_exp  = info.get("interestExpense", 0) or 0
        market_cap    = info.get("marketCap", 0) or 0

        debt_ratio     = total_debt / total_assets if total_assets else 0
        interest_ratio = abs(interest_exp) / total_revenue if total_revenue else 0

        return {
            "ticker":         ticker,
            "name":           info.get("longName", ticker),
            "sector":         info.get("sector", "غير محدد"),
            "industry":       info.get("industry", "غير محدد"),
            "price":          info.get("regularMarketPrice", 0),
            "change_pct":     info.get("regularMarketChangePercent", 0),
            "market_cap":     market_cap,
            "total_debt":     total_debt,
            "total_assets":   total_assets,
            "total_revenue":  total_revenue,
            "interest_exp":   abs(interest_exp),
            "debt_ratio":     debt_ratio,
            "interest_ratio": interest_ratio,
            "pe_ratio":       info.get("trailingPE", None),
            "description":    info.get("longBusinessSummary", "")[:300],
        }
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return None

# ─── دالة الفحص الشرعي ────────────────────────────────────────────
def halal_screen(data: dict) -> dict:
    sector   = data.get("sector", "")
    industry = data.get("industry", "")
    debt_r   = data.get("debt_ratio", 0)
    int_r    = data.get("interest_ratio", 0)

    # استبعاد فوري
    for h in HARAM_SECTORS:
        if h.lower() in sector.lower() or h.lower() in industry.lower():
            return {
                "status": "غير متوافق ❌",
                "score": 10,
                "color": "🔴",
                "issues": [f"القطاع محرم: {sector}"],
                "verdict": "مستبعد شرعياً بسبب طبيعة نشاطه الأساسي",
            }

    score = 100
    issues = []
    warnings = []

    # نسبة الديون الربوية
    if debt_r > 0.33:
        score -= 35
        issues.append(f"نسبة الديون الربوية {debt_r*100:.1f}% (الحد 33%)")
    elif debt_r > 0.20:
        score -= 10
        warnings.append(f"نسبة ديون مرتفعة نسبياً {debt_r*100:.1f}%")

    # نسبة إيرادات الفوائد
    if int_r > 0.05:
        score -= 30
        issues.append(f"إيرادات فوائد {int_r*100:.1f}% من الإيرادات (الحد 5%)")
    elif int_r > 0.03:
        score -= 10
        warnings.append(f"إيرادات فوائد تحتاج متابعة {int_r*100:.1f}%")

    # قطاعات تحتاج تدقيق
    for w in WARNING_SECTORS:
        if w.lower() in sector.lower():
            score -= 15
            warnings.append(f"قطاع {sector} يحتاج مراجعة شرعية دقيقة")

    score = max(0, score)

    if score >= 80:
        return {"status": "متوافق ✅", "score": score, "color": "🟢",
                "issues": warnings, "verdict": "يستوفي المعايير الشرعية الأساسية"}
    elif score >= 50:
        return {"status": "مشكوك فيه ⚠️", "score": score, "color": "🟡",
                "issues": issues + warnings, "verdict": "يحتاج مراجعة من عالم شرعي متخصص"}
    else:
        return {"status": "غير متوافق ❌", "score": score, "color": "🔴",
                "issues": issues, "verdict": "لا يستوفي المعايير الشرعية"}

# ─── تنسيق رسالة تحليل السهم ──────────────────────────────────────
def format_stock_message(data: dict, screen: dict) -> str:
    change_arrow = "📈" if data["change_pct"] >= 0 else "📉"
    change_sign  = "+" if data["change_pct"] >= 0 else ""
    cap_b = data["market_cap"] / 1e9 if data["market_cap"] else 0

    issues_text = ""
    if screen["issues"]:
        issues_text = "\n⚠️ *ملاحظات:*\n" + "\n".join(f"  • {i}" for i in screen["issues"])

    bar_filled = int(screen["score"] / 10)
    score_bar  = "█" * bar_filled + "░" * (10 - bar_filled)

    return f"""
{screen["color"]} *{data["name"]}*
`{data["ticker"]}`  |  قطاع: {data["sector"]}

💰 *السعر:* {data["price"]:.2f} جنيه  {change_arrow} {change_sign}{data["change_pct"]:.2f}%
🏢 *القيمة السوقية:* {cap_b:.1f} مليار جنيه

━━━━━━━━━━━━━━━━━━
📋 *الفحص الشرعي*
━━━━━━━━━━━━━━━━━━
الحالة: *{screen["status"]}*
الدرجة: `{score_bar}` {screen["score"]}/100

📊 *المؤشرات المالية:*
  • نسبة الديون: {data["debt_ratio"]*100:.1f}% (الحد: 33%)
  • نسبة إيرادات الفوائد: {data["interest_ratio"]*100:.1f}% (الحد: 5%)
{issues_text}

📝 *الحكم:* {screen["verdict"]}

⚠️ _هذا تحليل استرشادي وليس فتوى شرعية_
"""

# ─── استدعاء Claude للتحليل العميق ───────────────────────────────
def ask_claude(user_question: str, stock_context: str = "") -> str:
    system = """أنت خبير في الاستثمار الإسلامي والتحليل المالي للبورصة المصرية (EGX).
تساعد المستخدمين عبر Telegram في تطبيق Thndr.

معايير الفحص الشرعي التي تستخدمها (AAOIFI):
1. استبعاد: البنوك الربوية، الكحول، التبغ، الأسلحة، القمار، الترفيه المحرم
2. نسبة الديون الربوية < 33% من إجمالي الأصول
3. إيرادات الفوائد والمحرمات < 5% من إجمالي الإيرادات
4. الأصول الحلال > 80% من إجمالي الأصول

قواعد الرد:
- رد بالعربية دائماً
- رد موجز ومفيد (مناسب لتيليجرام)
- استخدم ✅ للمتوافق، ❌ لغير المتوافق، ⚠️ للمشكوك فيه
- نبّه دائماً أن تحليلك استرشادي وليس فتوى شرعية
- لا تتجاوز 300 كلمة في الرد"""

    messages = []
    if stock_context:
        messages.append({"role": "user", "content": f"سياق إضافي عن السهم:\n{stock_context}"})
        messages.append({"role": "assistant", "content": "تم استلام بيانات السهم، كيف يمكنني مساعدتك؟"})

    messages.append({"role": "user", "content": user_question})

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            system=system,
            messages=messages
        )
        return response.content[0].text
    except Exception as e:
        logger.error(f"Claude error: {e}")
        return "عذراً، حدث خطأ في الاتصال بالذكاء الاصطناعي. حاول مجدداً."

# ─── أوامر Telegram ───────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 فحص أسهم EGX", callback_data="screen_all")],
        [InlineKeyboardButton("🔍 تحليل سهم بعينه", callback_data="analyze_help")],
        [InlineKeyboardButton("📖 معايير الشريعة", callback_data="criteria")],
        [InlineKeyboardButton("⭐ أفضل الأسهم الحلال", callback_data="top_halal")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🌙 *أهلاً بك في @ELBorsaa\_halal\_bot*\n"
        "البورصة المصرية · EGX · Thndr\n\n"
        "يمكنني مساعدتك في:\n"
        "• فحص الأسهم شرعياً بمعايير AAOIFI\n"
        "• تحليل أي سهم عند الطلب\n"
        "• ترشيح الأسهم المتوافقة مع الشريعة\n\n"
        "اختر من القائمة أو أرسل رمز السهم مباشرة\n"
        "مثال: `SWDY` أو `TMGH`",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📌 *أوامر البوت:*\n\n"
        "/start — القائمة الرئيسية\n"
        "/screen — فحص شامل لأسهم EGX\n"
        "/top — أفضل الأسهم الحلال\n"
        "/criteria — معايير الفحص الشرعي\n"
        "/analyze XXXX — تحليل سهم (مثال: /analyze SWDY)\n\n"
        "أو فقط أرسل *رمز السهم* مباشرة!\n"
        "مثال: `TMGH` أو `SWDY.CA`",
        parse_mode="Markdown"
    )

async def screen_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.effective_message.reply_text(
        "🔍 جاري فحص أسهم البورصة المصرية...\nقد يستغرق هذا دقيقة واحدة ⏳"
    )

    results = {"halal": [], "doubtful": [], "haram": []}

    for ticker, arabic_name in list(EGX_STOCKS.items())[:8]:  # أول 8 أسهم
        data = get_stock_data(ticker)
        if not data:
            data = {"ticker": ticker, "name": arabic_name, "sector": "غير محدد",
                    "price": 0, "change_pct": 0, "market_cap": 0,
                    "debt_ratio": 0.1, "interest_ratio": 0.01, "total_debt": 0,
                    "total_assets": 1, "total_revenue": 1, "interest_exp": 0}
        screen = halal_screen(data)
        entry = f"{screen['color']} *{arabic_name}* (`{ticker.replace('.CA','')}`) — {screen['score']}/100"

        if "متوافق ✅" in screen["status"]:
            results["halal"].append(entry)
        elif "مشكوك" in screen["status"]:
            results["doubtful"].append(entry)
        else:
            results["haram"].append(entry)

    text = "📊 *نتائج الفحص الشرعي — البورصة المصرية*\n"
    text += "━━━━━━━━━━━━━━━━━━\n\n"

    if results["halal"]:
        text += f"✅ *متوافق مع الشريعة ({len(results['halal'])} سهم):*\n"
        text += "\n".join(results["halal"]) + "\n\n"

    if results["doubtful"]:
        text += f"⚠️ *مشكوك فيه ({len(results['doubtful'])} سهم):*\n"
        text += "\n".join(results["doubtful"]) + "\n\n"

    if results["haram"]:
        text += f"❌ *غير متوافق ({len(results['haram'])} سهم):*\n"
        text += "\n".join(results["haram"]) + "\n\n"

    text += "━━━━━━━━━━━━━━━━━━\n"
    text += "💡 أرسل رمز أي سهم للتحليل التفصيلي\n"
    text += "_⚠️ تحليل استرشادي وليس فتوى شرعية_"

    await msg.edit_text(text, parse_mode="Markdown")

async def top_halal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.effective_message.reply_text("⭐ جاري استخراج أفضل الأسهم الحلال...")

    scored = []
    for ticker, arabic_name in list(EGX_STOCKS.items())[:10]:
        data = get_stock_data(ticker) or {
            "ticker": ticker, "name": arabic_name, "sector": "غير محدد",
            "price": 0, "change_pct": 0, "market_cap": 0,
            "debt_ratio": 0.05, "interest_ratio": 0.01,
            "total_debt": 0, "total_assets": 1, "total_revenue": 1, "interest_exp": 0
        }
        screen = halal_screen(data)
        scored.append((arabic_name, ticker, screen["score"], screen["color"], data.get("price", 0), data.get("change_pct", 0)))

    scored.sort(key=lambda x: x[2], reverse=True)
    top5 = [s for s in scored if s[2] >= 50][:5]

    text = "⭐ *أفضل الأسهم المتوافقة مع الشريعة*\n━━━━━━━━━━━━━━━━━━\n\n"
    for i, (name, ticker, score, color, price, chg) in enumerate(top5, 1):
        arrow = "📈" if chg >= 0 else "📉"
        text += f"{i}. {color} *{name}*\n"
        text += f"   الرمز: `{ticker.replace('.CA','')}` | الدرجة: {score}/100\n"
        text += f"   السعر: {price:.2f} ج {arrow} {chg:+.2f}%\n\n"

    text += "━━━━━━━━━━━━━━━━━━\n"
    text += "💡 أرسل رمز أي سهم للتفاصيل الكاملة\n"
    text += "_⚠️ تحليل استرشادي وليس فتوى شرعية_"

    await msg.edit_text(text, parse_mode="Markdown")

async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📌 أرسل رمز السهم بعد الأمر\nمثال: `/analyze SWDY` أو `/analyze TMGH`",
            parse_mode="Markdown"
        )
        return
    ticker = context.args[0].upper()
    await analyze_stock(update, context, ticker)

async def analyze_stock(update: Update, context: ContextTypes.DEFAULT_TYPE, ticker: str):
    # نجرب مع وبدون .CA
    if not ticker.endswith(".CA"):
        ticker_ca = ticker + ".CA"
    else:
        ticker_ca = ticker
        ticker = ticker.replace(".CA", "")

    msg = await update.effective_message.reply_text(
        f"🔍 جاري تحليل سهم *{ticker}*...", parse_mode="Markdown"
    )

    data = get_stock_data(ticker_ca)
    if not data:
        # جرب بدون .CA
        data = get_stock_data(ticker)

    if not data:
        # استخدم Claude للرد
        answer = ask_claude(f"ما هو سهم {ticker} في البورصة المصرية؟ هل هو متوافق مع الشريعة الإسلامية؟")
        await msg.edit_text(answer)
        return

    screen = halal_screen(data)
    text = format_stock_message(data, screen)

    # زر لطلب تحليل أعمق
    keyboard = [[
        InlineKeyboardButton("🤖 تحليل AI أعمق", callback_data=f"deep_{ticker_ca}"),
        InlineKeyboardButton("📊 مقارنة بالقطاع", callback_data=f"compare_{data['sector']}"),
    ]]
    await msg.edit_text(text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard))

async def criteria_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """📖 *معايير الفحص الشرعي (AAOIFI)*
━━━━━━━━━━━━━━━━━━

🚫 *القطاعات المستبعدة كلياً:*
• البنوك والمؤسسات الربوية
• شركات التمويل بالفائدة
• الكحول والتبغ
• الأسلحة والقمار
• الترفيه والإعلام المحرم

📊 *المعايير الكمية:*
• نسبة الديون الربوية < 33% من الأصول
• إيرادات الفوائد < 5% من الإيرادات
• الأصول الحلال > 80% من إجمالي الأصول
• الذمم المدينة < 45% من القيمة السوقية

✅ *القطاعات المسموحة:*
• الصناعة والتصنيع
• العقارات والإنشاء
• الاتصالات والتقنية
• الصحة والدواء
• الأغذية الحلال
• الطاقة والبترول

⚠️ *القطاعات المشكوك فيها:*
• الخدمات المالية غير المصرفية
• التأمين التقليدي
• الفنادق والسياحة

━━━━━━━━━━━━━━━━━━
_المصدر: معايير AAOIFI ومؤشر داو جونز الإسلامي_
_⚠️ هذا البوت يقدم تحليلاً استرشادياً وليس فتوى شرعية_"""

    await update.effective_message.reply_text(text, parse_mode="Markdown")

# ─── معالج الرسائل النصية العادية ────────────────────────────────
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().upper()

    # إذا بدا كرمز سهم (2-6 أحرف)
    if 2 <= len(text) <= 6 and text.isalpha():
        await analyze_stock(update, context, text)
        return

    # سؤال عام → Claude
    thinking = await update.message.reply_text("🤔 جاري التفكير...")
    answer = ask_claude(update.message.text)
    await thinking.edit_text(answer)

# ─── معالج الأزرار ────────────────────────────────────────────────
async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "screen_all":
        await screen_command(update, context)
    elif data == "top_halal":
        await top_halal(update, context)
    elif data == "criteria":
        await criteria_command(update, context)
    elif data == "analyze_help":
        await query.message.reply_text(
            "📌 أرسل رمز السهم مباشرة في الشات\nمثال: `SWDY` أو `TMGH` أو `COMI`",
            parse_mode="Markdown"
        )
    elif data.startswith("deep_"):
        ticker = data.replace("deep_", "")
        stock_data = get_stock_data(ticker)
        context_str = str(stock_data) if stock_data else ""
        symbol = ticker.replace(".CA", "")
        answer = ask_claude(
            f"قدم تحليلاً شرعياً ومالياً عميقاً لسهم {symbol} في البورصة المصرية. "
            f"هل ينصح بالاستثمار فيه من الناحية الشرعية؟ وضح المخاطر والفرص.",
            context_str
        )
        await query.message.reply_text(f"🤖 *تحليل AI لسهم {symbol}:*\n\n{answer}", parse_mode="Markdown")
    elif data.startswith("compare_"):
        sector = data.replace("compare_", "")
        answer = ask_claude(
            f"قارن الأسهم المصرية في قطاع {sector} من ناحية التوافق الشرعي. "
            f"ما هي أفضل خيارات الاستثمار الحلال في هذا القطاع بالبورصة المصرية؟"
        )
        await query.message.reply_text(f"📊 *مقارنة قطاع {sector}:*\n\n{answer}", parse_mode="Markdown")

# ─── تشغيل البوت ──────────────────────────────────────────────────
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_command))
    app.add_handler(CommandHandler("screen",   screen_command))
    app.add_handler(CommandHandler("top",      top_halal))
    app.add_handler(CommandHandler("analyze",  analyze_command))
    app.add_handler(CommandHandler("criteria", criteria_command))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🌙 @ELBorsaa_halal_bot يعمل...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
