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


def create_driver():
    """创建稳定的 Chrome Driver"""
    options = Options()
    options.add_argument("--headless=new")  # 新版 Chrome 推荐
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def fetch_terror_info():
    """爬取恐怖地带信息（改自你 zip 里的原始逻辑）"""
    url = "https://d2tz.com/danger.html"  # ⚠️ 原代码的目标网址
    driver = create_driver()
    driver.get(url)
    time.sleep(3)  # 等页面加载

    html = driver.page_source
    driver.quit()

    soup = BeautifulSoup(html, "html.parser")

    # 解析城市和恐怖地带信息
    try:
        city = soup.select_one("div#ct").get_text(strip=True)
    except Exception:
        city = "未知"

    try:
        danger_zone = soup.select_one("div#c").get_text(strip=True)
    except Exception:
        danger_zone = "未知"

    try:
        next_city = soup.select_one("div#nt").get_text(strip=True)
    except Exception:
        next_city = "未知"

    try:
        next_danger_zone = soup.select_one("div#n").get_text(strip=True)
    except Exception:
        next_danger_zone = "未知"

    return city, danger_zone, next_city, next_danger_zone


def push_to_wechat(content):
    """推送消息到微信（ServerChan 示例）"""
    url = "https://sctapi.ftqq.com/YOUR_SENDKEY.send"  # ⚠️ 换成你自己的 ServerChan SendKey
    data = {
        "title": "恐怖地带预警",
        "desp": content
    }
    resp = requests.post(url, data=data)
    logger.info(f"推送结果: {resp.text}")


def _push_real_data():
    """定时任务：获取并推送数据"""
    try:
        city, danger_zone, next_city, next_danger_zone = fetch_terror_info()
        content = (
            f"当前城市：{city}\n"
            f"当前危险区域：{danger_zone}\n"
            f"下一个城市：{next_city}\n"
            f"下一个危险区域：{next_danger_zone}"
        )
        push_to_wechat(content)
    except Exception as e:
        logger.error(f"后台推送失败: {e}")


# Flask 路由
@app.route("/")
def index():
    return "恐怖地带推送服务运行中..."


# 启动定时任务
scheduler = BackgroundScheduler()
scheduler.add_job(_push_real_data, "interval", minutes=5)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
