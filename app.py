import os, requests, logging
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread
from selenium.common.exceptions import TimeoutException, WebDriverException

# 直接写死企业微信机器人地址
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    options = Options()
    options.binary_location = "/usr/bin/chromium-browser"  # 修正浏览器路径
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-images")
    options.add_argument("--window-size=800,600")
    options.page_load_strategy = "eager"  # 优化加载策略

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(15)  # 设置页面加载超时
    try:
        # 增加重试机制
        for _ in range(2):
            try:
                driver.get(TARGET_URL)
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "tbody[role='rowgroup'] tr"))
                )
                break
            except TimeoutException:
                logger.warning("重试页面加载...")
                continue

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
    except (TimeoutException, WebDriverException) as e:
        logger.error(f"抓取失败: {str(e)}")
        return None, None, None, None
    finally:
        driver.quit()

def send_wecom_message(c, ct, n, nt):
    now  = c or "暂无"
    soon = n or "暂无"
    content = f"{now}▶{soon}"
    try:
        rsp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=5)
        logger.info(f"WeCom response: {rsp.json()}")
    except Exception as e:
        logger.error(f"发送消息失败: {str(e)}")

@app.route("/")
def index():
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-d2tz is running!", 200

def _push_real_data():
    try:
        c, ct, n, nt = fetch_terror_info()
        if c or n:
            send_wecom_message(c, ct, n, nt)
        else:
            logger.warning("未获取到有效数据")
            send_wecom_message("获取失败", "", "获取失败", "")
    except Exception as e:
        logger.exception("后台推送失败")
        try:
            requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": "后台异常▶后台异常"}}, timeout=5)
        except Exception as e:
            logger.error(f"异常通知发送失败: {str(e)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # PORT仍保留环境变量（Render平台需要）
    app.run(host="0.0.0.0", port=port)
