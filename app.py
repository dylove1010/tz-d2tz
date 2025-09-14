import asyncio, logging, os
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask
from playwright.async_api import async_playwright
import requests

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"
WAIT_TIME   = 10

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app   = Flask(__name__)
sched = BackgroundScheduler()

async def fetch_terror_info():
    async with async_playwright() as p:
        # Render 装好的 chromium 路径
       browser = await p.chromium.launch(
    headless=True,
    args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
)
        page = await browser.new_page()
        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
        })
        for attempt in range(3):
            try:
                await page.goto(TARGET_URL, timeout=60000)
                break
            except Exception as e:
                logger.warning("访问页面失败 (%d/3): %s", attempt+1, e)
                if attempt == 2:
                    await browser.close(); return None,None,None,None
                await asyncio.sleep(2)
        try:
            await page.wait_for_selector("tbody[role='rowgroup'] tr", timeout=WAIT_TIME*1000)
            rows = await page.query_selector_all("tbody[role='rowgroup'] tr")
            results = []
            for row in rows:
                cells = await row.query_selector_all("td")
                if len(cells) >= 2:
                    time_text = (await cells[0].inner_text()).strip()
                    area_text = (await cells[1].inner_text()).strip()
                    results.append((time_text, area_text))
            await browser.close()
            if not results: return None,None,None,None
            next_time, next_area = results[0]
            current_time, current_area = results[1] if len(results)>1 else ("未知","未知")
            return current_area, current_time, next_area, next_time
        except Exception as e:
            logger.warning("抓取失败: %s", e)
            await browser.close(); return None,None,None,None

def send_wecom_message(c, ct, n, nt):
    ct_fmt = ct.replace("2025/", "") if ct else "信息未抓取到"
    nt_fmt = nt.replace("2025/", "") if nt else "信息未抓取到"
    content = (f"当前恐怖地带开始时间: {ct_fmt}\n"
               f"当前恐怖地带: 【{c or '信息未抓取到'}】\n"
               f"下一个恐怖地带开始时间: {nt_fmt}\n"
               f"下一个恐怖地带: 【{n or '信息未抓取到'}】")
    resp = requests.post(WEBHOOK_URL, json={"msgtype":"text","text":{"content":content}})
    logger.info("WeCom response: %s", resp.json())

async def main_job():
    logger.info("Scheduled task triggered")
    c,ct,n,nt = await fetch_terror_info()
    send_wecom_message(c,ct,n,nt)
    logger.info("Scheduled task completed")

# 定时任务
sched.add_job(lambda: asyncio.run(main_job()), "interval", hours=1, id="tz_job")
sched.start()

# 路由
@app.route("/")
def index(): return "TZ-bot is running!", 200

@app.route("/test")
def test(): asyncio.run(main_job()); return "manual trigger done", 200

# 启动
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
