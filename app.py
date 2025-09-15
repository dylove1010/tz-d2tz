import logging
import time
import requests
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fetch_terror_info():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")

    driver = webdriver.Chrome(options=options)
    driver.get("目标网址替换这里")  # 👈 换成你的恐怖地带页面
    time.sleep(3)

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")
    current = soup.select_one("当前恐怖地带的选择器").get_text(strip=True)
    next_ = soup.select_one("下一个恐怖地带的选择器").get_text(strip=True)
    return current, next_

def push_to_wecom(content):
    url = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=你的key"  # 👈 换成你自己的
    payload = {"msgtype": "text", "text": {"content": content}}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        logger.info(f"WeCom response: {resp.json()}")
    except Exception as e:
        logger.error(f"推送失败: {e}")

def _push_real_data():
    try:
        c, n = fetch_terror_info()
        msg = f"当前恐怖地带 ▶ {c}\n下一个恐怖地带 ▶ {n}"
        push_to_wecom(msg)
    except Exception as e:
        logger.error(f"后台推送失败: {e}")

@app.route("/")
def index():
    _push_real_data()
    return "OK"

if __name__ == "__main__":
    scheduler = BackgroundScheduler()
    scheduler.add_job(_push_real_data, "interval", minutes=5)
    scheduler.start()
    app.run(host="0.0.0.0", port=10000)
