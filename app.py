import os, requests, logging
from flask import Flask
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from threading import Thread

# 从环境变量读取企业微信机器人地址（更安全）
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644")
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    options = Options()
    # 修正：指向 Chromium 浏览器可执行文件（非驱动）
    options.binary_location = "/usr/bin/chromium-browser"
    # 启用新版 headless 模式（解决 DevToolsActivePort 问题）
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")  # 容器环境必需
    options.add_argument("--disable-dev-shm-usage")  # 解决共享内存限制
    options.add_argument("--remote-debugging-port=9222")  # 强制开启调试端口
    options.add_argument("--disable-gpu")  # 禁用 GPU 加速（无头模式不需要）
    options.add_argument("--window-size=1920,1080")  # 固定窗口大小，避免元素定位问题

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(TARGET_URL)
        # 等待表格加载（最长超时 15 秒，增加容错）
        WebDriverWait(driver, 15).until(
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
    try:
        rsp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=10)
        logger.info("WeCom response: %s", rsp.json())
    except Exception as e:
        logger.error("企业微信推送失败: %s", str(e))

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
        try:
            requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": "后台异常▶后台异常"}}, timeout=10)
        except Exception as push_err:
            logger.error("异常提示推送失败: %s", str(push_err))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))  # 默认端口改为 10000，与部署一致
    app.run(host="0.0.0.0", port=port)
