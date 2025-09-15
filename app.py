import asyncio
import logging
import requests
from flask import Flask
from playwright.async_api import async_playwright

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def fetch_terror_info():
    """抓取当前和下一个恐怖地带信息"""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(TARGET_URL, timeout=60000)
            # 等待表格
            await page.wait_for_selector("tbody[role='rowgroup'] tr", timeout=10000)
            rows = await page.query_selector_all("tbody[role='rowgroup'] tr")
            out = []
            for row in rows[:2]:
                cells = await row.query_selector_all("td")
                if len(cells) >= 2:
                    area_raw = (await cells[1].inner_text()).strip()
                    area_only = area_raw.split("▶")[-1].strip()  # 去掉前面的 Now / Coming soon
                    out.append(area_only)
            await browser.close()
            if len(out) < 2:
                return None, None
            # 页面最新的时间/区域在前
            next_area, current_area = out
            return current_area, next_area
    except Exception as e:
        logger.warning(f"抓取失败: {e}")
        return None, None

def send_wecom_message(current, next_):
    """推送企业微信"""
    current = current or "信息未抓取到"
    next_ = next_ or "信息未抓取到"
    content = f"{current} ▶ {next_}"
    try:
        resp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=5)
        logger.info(f"WeCom response: {resp.json()}")
    except Exception as e:
        logger.warning(f"WeCom 推送失败: {e}")

async def main_job():
    current, next_ = await fetch_terror_info()
    send_wecom_message(current, next_)

@app.route("/")
def index():
    # 异步执行，不阻塞
    asyncio.run(main_job())
    return "tz-bot is running!", 200

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
