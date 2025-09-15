import asyncio
import logging
from flask import Flask
from playwright.async_api import async_playwright
import requests

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def fetch_terror_info():
    """抓取前两个恐怖地带信息"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TARGET_URL, timeout=60000)
        await page.wait_for_selector("tbody[role='rowgroup'] tr", timeout=10000)
        rows = await page.query_selector_all("tbody[role='rowgroup'] tr")
        results = []
        for row in rows[:2]:
            cells = await row.query_selector_all("td")
            if len(cells) >= 2:
                area_raw = (await cells[1].inner_text()).strip()
                # 去掉 "Now▶" / "Coming soon▶"
                area_only = area_raw.split("▶")[-1].strip()
                results.append(area_only)
        await browser.close()
        if len(results) < 2:
            return "未获取到信息", "未获取到信息"
        return results[0], results[1]

def send_wecom_message(current, next_):
    content = f"{current} ▶ {next_}"
    try:
        resp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=10)
        logger.info("WeCom response: %s", resp.json())
    except Exception as e:
        logger.error("WeCom push failed: %s", e)

async def main_job():
    current, next_ = await fetch_terror_info()
    send_wecom_message(current, next_)

@app.route("/")
def index():
    # 异步执行，不阻塞 Render 健康检查
    asyncio.run(main_job())
    return "tz-bot running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(10000))
