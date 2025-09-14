import asyncio
import logging
import os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from playwright.async_api import async_playwright
import requests
import re

# --- 配置 ---
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "你的企业微信Webhook")
TARGET_URL = "https://www.d2tz.info/?l=zh-cn"
WAIT_TIME = 15  # 页面渲染等待时间（秒）

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
scheduler = BackgroundScheduler()

async def fetch_terror_info():
    """抓取当前和下一个恐怖区域信息"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # Render环境必须headless
        page = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/140.0.0.0 Safari/537.36"
        })

        # 重试访问页面
        for attempt in range(3):
            try:
                await page.goto(TARGET_URL, timeout=60000, wait_until='load')
                break
            except Exception as e:
                logger.warning(f"访问页面失败 ({attempt+1}/3): {e}")
                if attempt == 2:
                    await browser.close()
                    return None, None, None, None
                await asyncio.sleep(2)

        # 等待表格渲染
        try:
            await page.wait_for_selector("tbody[role='rowgroup'] tr", timeout=WAIT_TIME*1000)
            rows = await page.query_selector_all("tbody[role='rowgroup'] tr")
            results = []

            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 2:
                    time_text = (await cells[0].inner_text()).strip()
                    area_text = (await cells[1].inner_text()).strip()
                    area_text = re.sub(r'Coming soon|Now', '', area_text, flags=re.IGNORECASE).strip()
                    results.append((time_text, area_text))

            await browser.close()

            if not results:
                return None, None, None, None

            # 下一个恐怖地带排在最前面
            next_time, next_area = results[0]
            current_time, current_area = results[1] if len(results) > 1 else ("未知", "未知")
            return current_area, current_time, next_area, next_time
        except Exception as e:
            logger.warning(f"抓取失败: {e}")
            await browser.close()
            return None, None, None, None

def send_wecom_message(current, current_time, next_, next_time):
    """推送文字消息到企业微信"""
    msg_lines = [
        f"当前恐怖地带开始时间: {current_time or '信息未抓取到'}",
        f"当前恐怖地带: 【{current or '信息未抓取到'}】",
        f"下一个恐怖地带开始时间: {next_time or '信息未抓取到'}",
        f"下一个恐怖地带: 【{next_ or '信息未抓取到'}】"
    ]

    data = {"msgtype": "text", "text": {"content": "\n".join(msg_lines)}}
    try:
        resp = requests.post(WEBHOOK_URL, json=data)
        logger.info(f"Sent message to WeCom, response: {resp.json()}")
    except Exception as e:
        logger.warning(f"推送失败: {e}")

async def main_job():
    logger.info("Scheduled task triggered")
    current, current_time, next_, next_time = await fetch_terror_info()
    send_wecom_message(current, current_time, next_, next_time)
    logger.info("Scheduled task completed")

# 定时任务，每小时抓取一次
scheduler.add_job(lambda: asyncio.run(main_job()), "interval", hours=1, id="scheduled_task")
scheduler.start()

# Flask路由
@app.route("/test")
def test_push():
    asyncio.run(main_job())
    return "手动测试推送触发", 200

@app.route("/")
def index():
    return "Terror Zone WeCom Bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info("Starting Flask app with scheduler...")
    app.run(host="0.0.0.0", port=port)
