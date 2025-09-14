import os, requests, logging
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    options = Options()
    options.binary_location = "/usr/bin/chromium-driver"
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--single-process")
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
                out.append((cells[0].text.strip(), cells[1].text.strip()))
        if len(out) < 2:
            return None, None, None, None
        next_time, next_area = out[0]
        current_time, current_area = out[1]
        return current_area, current_time, next_area, next_time
    finally:
        driver.quit()

def send_wecom_message(c, ct, n, nt):
    now  = c or "暂无"
    soon = n or "暂无"
    content = f"{c or '暂无'}▶{n or '暂无'}"   # 纯区域
    rsp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}})
    logger.info("WeCom response: %s", rsp.json())

# ---------- 启动即推 ----------
with app.app_context():
    c, ct, n, nt = fetch_terror_info()
    if c or n:
        send_wecom_message(c, ct, n, nt)
# ------------------------------

@app.route("/")
def index():
    return "tz-bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
