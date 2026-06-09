import asyncio
import logging
import sys
import time
import os  # تمت الإضافة
from typing import Dict, List, Set

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties

# ═════════════════════ إعدادات السجل ═════════════════════
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("bot_errors.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("JoshuaXAI_Ultimate")

# ═════════════════════ مفاتيح التشغيل (مستوردة بأمان من البيئة) ═════════════════════
API_TOKEN = os.environ.get("API_TOKEN")
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
JOSHUA_ACCOUNT = "@Jo8shua"
ADMIN_IDS = {8507987505}

# ═════════════════════ إعدادات OpenRouter (محسّنة) ═════════════════════
MODEL_NAME = "deepseek/deepseek-chat"
REQUEST_TIMEOUT = 60
RETRY_MAX = 4
BASE_DELAY = 2

# قائمة الـ 10 مشاريع (بدون سعر الدولار)
PROJECTS = [
    {"name": "بوت تيليجرام عادي", "price_syp": 150000, "days": "3-5 أيام", "desc": "بوت بسيط مع أزرار وردود تلقائية"},
    {"name": "بوت تيليجرام متطور (AI)", "price_syp": 300000, "days": "5-7 أيام", "desc": "بوت ذكي يفهم المحادثات ويرد مثل الإنسان"},
    {"name": "سحب بيانات (Scraping) إلى Excel", "price_syp": 200000, "days": "3-5 أيام", "desc": "برنامج يسحب بيانات من مواقع ويضعها في Excel"},
    {"name": "سحب بيانات لقواعد البيانات", "price_syp": 350000, "days": "5-7 أيام", "desc": "نظام آلي يسحب البيانات ويخزنها في قاعدة بيانات"},
    {"name": "أتمتة مهام (صغير)", "price_syp": 250000, "days": "4-6 أيام", "desc": "أتمتة مهمة واحدة أو اثنتين"},
    {"name": "أتمتة مهام متوسطة", "price_syp": 400000, "days": "7-10 أيام", "desc": "أتمتة عدة مهام مع تقارير"},
    {"name": "موقع ويب بسيط", "price_syp": 500000, "days": "5-7 أيام", "desc": "موقع تعريفي أو مدونة بعدة صفحات"},
    {"name": "متجر إلكتروني كامل", "price_syp": 1000000, "days": "10-14 يوم", "desc": "متجر مع سلة شراء ودفع إلكتروني"},
    {"name": "تطبيق موبايل بسيط", "price_syp": 2000000, "days": "14-21 يوم", "desc": "تطبيق أندرويد/iOS بوظائف أساسية"},
    {"name": "استشارات تقنية (ساعة)", "price_syp": 50000, "days": "فورية", "desc": "جلسة استشارة صوتية أو كتابية لمدة ساعة"},
]

# ═════════════════════ تعليمة النظام (بدون ذكر Syrian Lancer كمشروع) ═════════════════════
SYSTEM_PROMPT = (
    "أنت (Joshua X-AI Ultimate)، مساعد ذكي ثنائي اللغة، تم تطويرك على يد المطور جوشوا. "
    "أنت خبير في البرمجة، التقنية، والذكاء الاصطناعي، وهدفك مساعدة المستخدمين بأفضل صورة.\n\n"
    "**تعليمات اللغة:** إذا كتب المستخدم بالعربية، أجب بالعربية. إذا كتب بالإنجليزية، أجب بالإنجليزية. "
    "إذا استخدم مزيجاً، اختر اللغة الغالبة. اجعل ردودك طبيعية ومفصلة وودودة.\n\n"
    "**قائمة الخدمات والأسعار:**\n" +
    "\n".join([f"   - {p['name']}: {p['price_syp']:,} ل.س - {p['desc']}. المدة: {p['days']}." for p in PROJECTS]) +
    "\n\nطرق الدفع المتاحة:\n"
    f"   • شام كاش: دفع إلكتروني فوري.\n"
    f"   • تطبيق Syrian Lancer: وسيط ضامن (Escrow).\n"
    f"   • حوالات مالية: شركة الهرم أو بنك بيمو (BEMO).\n"
    f"📞 للتواصل مع المطور: {JOSHUA_ACCOUNT}\n\n"
    "**أسلوبك:** أنت خبير تقني، أجب بشرح وافٍ، وتذكر السياق (آخر 30 رسالة). "
    "في نهاية كل رد (إذا كان الموضوع يخص خدمات أو مشاريع)، شجّع المستخدم بلطف على التواصل مع المطور. "
    "لا تبالغ في الترويج، وكن صادقاً ومفيداً."
)

# ═════════════════════ العميل ═════════════════════
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

conversations: Dict[int, List[dict]] = {}
all_users: Set[int] = set()

# ──────────────────────────────
# أمر /start (بدون زر Syrian Lancer)
# ──────────────────────────────
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    all_users.add(message.chat.id)
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 استشارة ذكية / صيانة", callback_data="btn_ai"))
    builder.row(types.InlineKeyboardButton(text="💰 قائمة الأسعار (10 مشاريع)", callback_data="btn_prices"))
    builder.row(types.InlineKeyboardButton(text="💳 طرق الدفع", callback_data="btn_pay"))
    builder.row(types.InlineKeyboardButton(text="📞 تواصل مع المطور", url=f"https://t.me/{JOSHUA_ACCOUNT.replace('@','')}"))
    builder.row(types.InlineKeyboardButton(text="🌐 English / العربية", callback_data="btn_lang"))

    await message.reply(
        f"💻 <b>مرحباً بك في Joshua X-AI Ultimate – البوت الأسطوري!</b>\n\n"
        f"أنا هنا لخدمتك في كل ما يخص البرمجة والتقنية، وأتكلم العربية والإنجليزية.\n"
        f"• /projects – عرض الـ 10 مشاريع بالأسعار.\n"
        f"• /clear – مسح ذاكرة المحادثة.\n"
        f"• /ping – فحص سرعة الاستجابة.\n\n"
        f"📞 المطور: {JOSHUA_ACCOUNT}",
        reply_markup=builder.as_markup()
    )

# ──────────────────────────────
# ضغطات الأزرار (تم حذف btn_lancer)
# ──────────────────────────────
@dp.callback_query(F.data.startswith("btn_"))
async def handle_buttons(callback: types.CallbackQuery):
    data = callback.data
    if data == "btn_ai":
        await callback.message.reply("🧠 <b>نظام التشخيص الفوري نشط:</b>\nاكتب مشكلتك التقنية أو استفسارك وسأقوم بتحليلها وحلها فوراً.")
    elif data == "btn_prices":
        await send_projects_list(callback.message)
    elif data == "btn_pay":
        await callback.message.reply(
            f"💳 <b>طرق الدفع المتاحة:</b>\n\n"
            f"• <b>شام كاش:</b> دفع إلكتروني فوري.\n"
            f"• <b>تطبيق Syrian Lancer:</b> وسيط ضامن (Escrow).\n"
            f"• <b>حوالات مالية:</b> شركة الهرم أو بنك بيمو (BEMO).\n\n"
            f"📞 للتنسيق: {JOSHUA_ACCOUNT}"
        )
    elif data == "btn_lang":
        await callback.message.reply("🌐 <b>أنا ثنائي اللغة!</b> اكتب سؤالك بالعربية أو الإنجليزية وسأجيبك بنفس اللغة. جرب!")
    await callback.answer()

# ──────────────────────────────
# أمر /projects
# ──────────────────────────────
@dp.message(Command("projects"))
async def cmd_projects(message: types.Message):
    await send_projects_list(message)

async def send_projects_list(target: types.Message):
    text = "📋 <b>أفضل 10 مشاريع تقنية أقدمها:</b>\n\n"
    for i, p in enumerate(PROJECTS, 1):
        text += f"{i}. <b>{p['name']}</b>\n   💰 {p['price_syp']:,} ل.س | ⏳ {p['days']}\n   📝 {p['desc']}\n\n"
    text += f"📞 تواصل مع المطور: {JOSHUA_ACCOUNT}"
    await target.reply(text)

# ──────────────────────────────
# أوامر إضافية
# ──────────────────────────────
@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    if conversations.pop(message.chat.id, None):
        await message.reply("✅ تم مسح ذاكرة المحادثة.")
    else:
        await message.reply("ℹ️ لا توجد ذاكرة سابقة.")

@dp.message(Command("ping"))
async def cmd_ping(message: types.Message):
    start = time.time()
    msg = await message.reply("🏓 بنج...")
    latency = (time.time() - start) * 1000
    await msg.edit_text(f"🏓 بونج! {latency:.1f} ملي ثانية")

@dp.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("⛔ هذا الأمر للمطور فقط.")
    text = message.text.partition(" ")[2]
    if not text:
        return await message.reply("⚠️ اكتب الرسالة بعد الأمر.")
    count = 0
    for uid in list(all_users):
        try:
            await bot.send_message(uid, f"📣 <b>رسالة من المطور:</b>\n\n{text}")
            count += 1
        except:
            pass
    await message.reply(f"✅ تم الإرسال إلى {count} مستخدم.")

# ═════════════════════ المعالج الذكي ═════════════════════
@dp.message(F.text)
async def handle_text(message: types.Message):
    chat_id = message.chat.id
    user_text = message.text.strip()
    all_users.add(chat_id)

    await bot.send_chat_action(chat_id, "typing")

    add_to_history(chat_id, "user", user_text)
    contents = build_contents(chat_id)

    ai_text = await call_openrouter(contents)

    add_to_history(chat_id, "model", ai_text)
    await send_long_message(message, ai_text)

@dp.message(F.photo | F.document | F.video | F.audio | F.voice)
async def handle_media(message: types.Message):
    all_users.add(message.chat.id)
    await message.reply("⚠️ <b>أستطيع قراءة النصوص فقط حالياً.</b>\nاكتب سؤالك كتابةً وسأجيبك.")

# ═════════════════════ دوال الذاكرة (30 رسالة) ═════════════════════
MAX_HISTORY = 30

def add_to_history(chat_id: int, role: str, text: str):
    if chat_id not in conversations:
        conversations[chat_id] = []
    conversations[chat_id].append({"role": role, "text": text})
    if len(conversations[chat_id]) > MAX_HISTORY:
        conversations[chat_id].pop(0)

def build_contents(chat_id: int) -> list:
    history = conversations.get(chat_id, [])
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history:
        role = "user" if msg["role"] == "user" else "assistant"
        messages.append({"role": role, "content": msg["text"]})
    return messages

# ═════════════════════ استدعاء OpenRouter ═════════════════════
async def call_openrouter(messages: list) -> str:
    import aiohttp
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    last_exception = None
    for attempt in range(1, RETRY_MAX + 1):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter error (محاولة {attempt}): {response.status} - {error_text}")
                        if attempt < RETRY_MAX:
                            await asyncio.sleep(BASE_DELAY * attempt)
                        else:
                            last_exception = f"HTTP {response.status}"
        except Exception as e:
            logger.error(f"OpenRouter exception (محاولة {attempt}): {e}")
            if attempt < RETRY_MAX:
                await asyncio.sleep(BASE_DELAY * attempt)
            else:
                last_exception = str(e)
    
    return (
        "⚠️ <b>واجهتني مشكلة مؤقتة في الرد.</b>\n"
        f"السبب: {last_exception}\n"
        "حاول مرة أخرى بعد لحظات."
    )

# ═════════════════════ تقسيم الرسائل الطويلة ═════════════════════
async def send_long_message(original_msg: types.Message, text: str):
    max_len = 4000
    if len(text) <= max_len:
        await original_msg.reply(text)
    else:
        parts = []
        while len(text) > max_len:
            split_idx = text.rfind('\n', 0, max_len)
            if split_idx == -1:
                split_idx = text.rfind(' ', 0, max_len)
            if split_idx == -1:
                split_idx = max_len
            parts.append(text[:split_idx])
            text = text[split_idx:].lstrip()
        if text:
            parts.append(text)
        for part in parts:
            await original_msg.reply(part)

# ═════════════════════ حلقة التشغيل الأبدية ═════════════════════
async def main():
    logger.info("🚀 Joshua X-AI Ultimate – البوت الأسطوري يعمل بدون Syrian Lancer...")
    retry_delay = 2
    while True:
        try:
            await dp.start_polling(bot, skip_updates=True, handle_signals=False)
        except asyncio.CancelledError:
            logger.info("تم إيقاف البوت.")
            break
        except Exception as e:
            logger.critical(f"خطأ جسيم: {e}", exc_info=True)
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)
            await bot.session.close()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 تم إيقاف البوت يدوياً.")
