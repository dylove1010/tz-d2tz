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

# ---------------- 配置 WeCom ----------------
CORP_ID = "你的企业ID"
AGENT_ID = "1000002"
SECRET = "你的应用Secret"
TO_USER = "@all"

def get_access_token():
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={CORP_ID}&corpsecret={SECRET}"
    resp = requests.get(url).json()
    return resp["access_token"]

def send_wecom_message(content):
    try:
        token = get_access_token()
        url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
        payload = {
            "touser": TO_USER,
            "msgtype": "text",
            "agentid": AGENT_ID,
            "text": {"content": content},
            "safe": 0
        }
        resp = requests.post(url, json=payload).json()
        logger.info(f"WeCom response: {resp}")
    except Exception as e:
        logger.error(f"推送失败: {e}")

# ---------------- 爬虫核心 ----------------
def fetch_terror_info():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")
    # 解决 Render DNS 问题
    options.add_argument("--host-resolver-rules=MAP * 8.8.8.8")

    driver = webdriver.Chrome(options=options)

    try:
        url = "https://d2.tzdata.org/"  # 你要爬的页面
        driver.get(url)
        time.sleep(3)

        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        # 解析恐怖地带
        current = soup.select_one("#current-terror")
        next_ = soup.select_one("#next-terror")

        current_text = current.get_text(strip=True) if current else "未获取到"
        next_text = next_.get_text(strip=True) if next_ else "未获取到"

        return current_text, next_text
    finally:
        driver.quit()

# ---------------- 定时任务 ----------------
def _push_real_data():
    try:
        c, n = fetch_terror_info()
        msg = f"当前恐怖地带 ▶ {c}\n下一个恐怖地带 ▶ {n}"
        send_wecom_message(msg)
    except Exception as e:
        logger.error(f"后台推送失败: {e}")

scheduler = BackgroundScheduler(timezone="UTC")
scheduler.add_job(_push_real_data, "interval", minutes=5)
scheduler.start()

# ---------------- Flask ----------------
@app.route("/")
def index():
    try:
        c, n = fetch_terror_info()
        msg = f"当前恐怖地带 ▶ {c}\n下一个恐怖地带 ▶ {n}"
        return msg
    except Exception as e:
        logger.error(f"前台获取失败: {e}")
        return "【获取失败】"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
