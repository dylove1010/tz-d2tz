import os
import asyncio
import logging
from flask import Flask
from playwright.async_api import async_playwright
import requests

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"
TARGET_URL = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def fetch_terror_info():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(TARGET_URL, timeout=60000)
        await page.wait_for_selector("tbody[role='rowgroup'] tr", timeout=10000)

        rows = await page.query_selector_all("tbody[role='rowgroup'] tr")
        out = []
        for row in rows[:2]:
            cells = await row.query_selector_all("td")
            if len(cells) >= 2:
                area_raw = (await cells[1].inner_text()).strip()
                area_only = area_raw.split("▶")[-1]
                out.append(area_only)

        await browser.close()

        if len(out) < 2:
            return None, None
        next_area, current_area = out
        return current_area, next_area

def send_wecom_message(current, next_):
    current = current or "信息未抓取到"
    next_ = next_ or "信息未抓取到"
    content = f"{current}▶{next_}"
    try:
        resp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=5)
        logger.info("WeCom response: %s", resp.json())
    except Exception as e:
        logger.warning(f"WeCom 推送失败: {e}")

async def main_job():
    logger.info("Scheduled task triggered")
    current, next_ = await fetch_terror_info()
    send_wecom_message(current, next_)
    logger.info("Scheduled task completed")

@app.route("/")
def index():
    asyncio.run(main_job())
    return "tz-d2tz bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
