import os
import requests
import logging
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread
from selenium.common.exceptions import TimeoutException

# 从环境变量读取配置（优先环境变量，兼容硬编码备用）
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644")
TARGET_URL = "https://www.d2tz.info/?l=zh-cn"

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    options = Options()
    # 浏览器配置（核心优化）
    options.binary_location = "/usr/bin/chromium-browser"  # 修正浏览器路径
    options.add_argument("--headless=new")  # 新版无头模式
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")  # 解决共享内存不足
    options.add_argument("--blink-settings=imagesEnabled=false")  # 禁用图片
    options.add_argument("--disable-javascript")  # 禁用JS（非必要时）
    options.add_argument("--disable-plugins")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=800,600")
    options.page_load_strategy = "eager"  # 只等待DOM加载完成

    # 初始化驱动并设置超时
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(15)  # 页面加载超时
    driver.set_script_timeout(10)     # JS执行超时

    try:
        driver.get(TARGET_URL)
        # 缩短等待时间，只等待关键元素
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody[role='rowgroup'] tr"))
        )
        # 提取数据
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody[role='rowgroup'] tr")[:2]
        out = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                area_raw = cells[1].text.strip()
                area_only = area_raw.split("▶")[-1].strip()
                out.append((cells[0].text.strip(), area_only))
        if len(out) < 2:
            return None, None, None, None
        next_time, next_area = out[0]
        current_time, current_area = out[1]
        return current_area, current_time, next_area, next_time
    except TimeoutException:
        logger.error("页面加载超时，未能获取数据")
        return None, None, None, None
    finally:
        driver.quit()  # 确保浏览器关闭

def send_wecom_message(c, ct, n, nt):
    now = c or "暂无"
    soon = n or "暂无"
    content = f"{now}▶{soon}"
    try:
        rsp = requests.post(WEBHOOK_URL, json={
            "msgtype": "text", 
            "text": {"content": content}
        }, timeout=5)
        logger.info("企业微信推送成功: %s", rsp.json())
    except Exception as e:
        logger.error("企业微信推送失败: %s", e)

def _push_real_data():
    max_retries = 2  # 重试机制
    for retry in range(max_retries):
        try:
            c, ct, n, nt = fetch_terror_info()
            if c or n:
                send_wecom_message(c, ct, n, nt)
                return
            logger.warning("第%d次尝试未获取到有效数据", retry + 1)
        except Exception as e:
            logger.warning("第%d次尝试失败: %s", retry + 1, e)
        # 重试间隔
        if retry < max_retries - 1:
            import time
            time.sleep(2)
    # 所有重试失败
    logger.error("所有重试均失败，发送异常通知")
    requests.post(WEBHOOK_URL, json={
        "msgtype": "text", 
        "text": {"content": "抓取超时▶抓取超时"}
    }, timeout=5)

@app.route("/")
def index():
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-d2tz is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
