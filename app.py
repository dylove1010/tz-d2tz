# app.py
import os
import logging
import requests
from flask import Flask
from threading import Thread
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key")
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)
app = Flask(__name__)

def fetch_terror_info():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(TARGET_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody[role='rowgroup'] tr"))
        )
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody[role='rowgroup'] tr")[:2]
        out = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                # 清理文本，去掉 "Coming soon / Now"
                area_text = cells[1].text.strip().replace("Coming soon", "").replace("Now", "").strip()
                out.append((cells[0].text.strip(), area_text))
        if len(out) < 2:
            return None, None, None, None
        # 当前 = 第 1 个生效的，下一个 = 第 2 个
        next_time, next_area = out[0]
        current_time, current_area = out[1]
        return current_area, current_time, next_area, next_time
    except Exception as e:
        logger.warning(f"抓取失败: {e}")
        return None, None, None, None
    finally:
        driver.quit()

def send_wecom_message(current, current_time, next_, next_time):
    msg_lines = []
    current_time_fmt = current_time or "信息未抓取到"
    next_time_fmt    = next_time or "信息未抓取到"
    current_area_fmt = f"【{current}】" if current else "暂无"
    next_area_fmt    = f"【{next_}】" if next_ else "暂无"

    msg_lines.append(f"当前恐怖地带开始时间: {current_time_fmt}")
    msg_lines.append(f"当前恐怖地带: {current_area_fmt}")
    msg_lines.append(f"下一个恐怖地带开始时间: {next_time_fmt}")
    msg_lines.append(f"下一个恐怖地带: {next_area_fmt}")

    data = {"msgtype": "text", "text": {"content": "\n".join(msg_lines)}}
    try:
        resp = requests.post(WEBHOOK_URL, json=data, timeout=5)
        logger.info(f"WeCom response: {resp.json()}")
    except Exception as e:
        logger.warning(f"WeCom 推送失败: {e}")

def push_job():
    current, current_time, next_, next_time = fetch_terror_info()
    if not current and not next_:
        logger.info("未获取到信息，发送占位")
        requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": "后台▶后台"}}, timeout=5)
    else:
        send_wecom_message(current, current_time, next_, next_time)

@app.route("/")
def index():
    Thread(target=push_job, daemon=True).start()
    return "tz-bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
