import os, requests, logging
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread

# 已设置为你的 WEBHOOK_URL
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    options = Options()
    # 关键修正：指向浏览器主程序（而非驱动）
    options.binary_location = "/usr/bin/chromium"  # 原先是 /usr/bin/chromium-driver（错误）
    # 启用新版无头模式（内存更低）
    options.add_argument("--headless=new")  # 原先是 --headless（旧模式）
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    # 新增内存优化参数
    options.add_argument("--disable-images")  # 禁止加载图片，减少内存
    options.add_argument("--window-size=800,600")  # 缩小窗口尺寸

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

def send_wecom_message(c, ct, n, nt):
    now  = c or "暂无"
    soon = n or "暂无"
    content = f"{now}▶{soon}"
    rsp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=5)
    logger.info("WeCom response: %s", rsp.json())

@app.route("/")
def index():
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-d2tz is running!", 200

def _push_real_data():
    try:
        c, ct, n, nt = fetch_terror_info()
        if c or n:
            send_wecom_message(c, ct, n, nt)
    except Exception as e:
        logger.exception("后台推送失败: %s", e)
        requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": "后台异常▶后台异常"}}, timeout=5)

if __name__ == "__main__":
    # 端口默认值改为 10000（与 Render 要求一致）
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
