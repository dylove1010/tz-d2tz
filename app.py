import asyncio
import logging
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TARGET_URL = "https://your-target-url-here.com"
WECHAT_URL = "https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token=xxx"
CHAT_ID = "xxx"


def fetch_terror_info():
    options = Options()
    options.add_argument("--headless=new")  # 新版 headless
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")  # 避免 DevToolsActivePort 错误

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(TARGET_URL)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody[role='rowgroup'] tr"))
        )
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody[role='rowgroup'] tr")[:2]
        out = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                area_raw = cells[1].text.strip()
                area_only = area_raw.split("▶")[-1]
                out.append((cells[0].text.strip(), area_only))
        if len(out) < 2:
            return None, None, None, None
        next_time, next_area = out[0]
        current_time, current_area = out[1]
        return current_area, current_time, next_area, next_time
    finally:
        driver.quit()


def push_to_wechat(msg: str):
    payload = {
        "touser": CHAT_ID,
        "msgtype": "text",
        "agentid": 1000002,
        "text": {"content": msg},
        "safe": 0,
    }
    try:
        r = requests.post(WECHAT_URL, json=payload)
        logger.info("WeCom response: %s", r.json())
    except Exception as e:
        logger.error("后台推送失败: %s", e)


def _push_real_data():
    try:
        c, ct, n, nt = fetch_terror_info()
        if not all([c, ct, n, nt]):
            msg = "当前恐怖地带: 信息未抓取到\n▶ 下一个恐怖地带: 信息未抓取到"
        else:
            msg = f"当前恐怖地带: {c}\n▶ 下一个恐怖地带: {n}"
        push_to_wechat(msg)
    except Exception as e:
        logger.error("后台推送失败: %s", e)


@app.route("/")
def index():
    _push_real_data()
    return "OK"


if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(_push_real_data, "interval", minutes=5)
    scheduler.start()
    app.run(host="0.0.0.0", port=10000)
