import os
import asyncio
import logging
import requests
from flask import Flask
from playwright.async_api import async_playwright

# --- 配置 ---
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL = "https://www.d2tz.info/?l=zh-cn"
WAIT_TIME = 10  # 页面渲染等待秒数

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

async def fetch_terror_info():
    """抓取当前和下一个恐怖地带"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)  # headless 模式，不弹出浏览器
        page = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/140.0.0.0 Safari/537.36"
        })

        try:
            await page.goto(TARGET_URL, timeout=60000)
            await page.wait_for_selector("tbody[role='rowgroup'] tr", timeout=WAIT_TIME*1000)

            rows = await page.query_selector_all("tbody[role='rowgroup'] tr")
            out = []
            for row in rows[:2]:  # 只取前两行
                cells = await row.query_selector_all("td")
                if len(cells) >= 2:
                    area_raw = await cells[1].inner_text()
                    # 去掉 "Now" / "Coming soon" 等文字
                    area_clean = area_raw.replace("Now", "").replace("Coming soon", "").strip()
                    out.append(area_clean)

            if len(out) < 2:
                return None, None
            # 页面最新的时间在最前面，第一行是下一个恐怖地带，第二行是当前
            next_area, current_area = out[0], out[1]
            return current_area, next_area

        except Exception as e:
            logger.warning(f"抓取失败: {e}")
            return None, None
        finally:
            await browser.close()

def send_wecom_message(current, next_):
    """推送企业微信消息"""
    current_text = current or "信息未获取到"
    next_text = next_ or "信息未获取到"
    content = f"{current_text} ▶ {next_text}"
    try:
        resp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=5)
        logger.info(f"WeCom response: {resp.json()}")
    except Exception as e:
        logger.warning(f"WeCom推送失败: {e}")

async def main_job():
    current, next_ = await fetch_terror_info()
    send_wecom_message(current, next_)

@app.route("/")
def index():
    # 异步线程触发抓取推送，不阻塞 Render 健康检查
    asyncio.run(main_job())
    return "tz-bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
