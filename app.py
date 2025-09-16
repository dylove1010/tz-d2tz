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

# 从环境变量读取Webhook地址（优先于硬编码）
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")  # 从环境变量获取
TARGET_URL = "https://www.d2tz.info/?l=zh-cn"

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    """抓取恐怖地带信息（优化浏览器配置）"""
    options = Options()
    # 关键：使用正确的Chromium浏览器路径（非驱动路径）
    options.binary_location = "/usr/bin/chromium-browser"
    # 内存优化参数
    options.add_argument("--headless=new")  # 新版无头模式（更省内存）
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--blink-settings=imagesEnabled=false")  # 禁用图片
    options.add_argument("--no-zygote")  # 减少进程
    options.add_argument("--single-process")  # 单进程模式

    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(TARGET_URL)
        # 缩短等待时间，避免不必要的内存占用
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody[role='rowgroup'] tr"))
        )
        # 只抓取前2行数据
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody[role='rowgroup'] tr")[:2]
        out = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                area_raw = cells[1].text.strip()
                area_only = area_raw.split("▶")[-1].strip()  # 提取纯区域名
                out.append((cells[0].text.strip(), area_only))
        
        # 数据格式化
        if len(out) >= 2:
            next_time, next_area = out[0]
            current_time, current_area = out[1]
            return current_area, current_time, next_area, next_time
        return None, None, None, None
    except Exception as e:
        logger.error("抓取数据失败: %s", str(e))
        return None, None, None, None
    finally:
        if driver:
            driver.quit()  # 确保浏览器进程关闭

def send_wecom_message(c, ct, n, nt):
    """发送企业微信消息"""
    if not WEBHOOK_URL:
        logger.error("未配置WEBHOOK_URL，无法推送")
        return
    
    now = c or "暂无"
    soon = n or "暂无"
    content = f"{now}▶{soon}"
    try:
        rsp = requests.post(
            WEBHOOK_URL,
            json={"msgtype": "text", "text": {"content": content}},
            timeout=5
        )
        logger.info(f"推送结果: {rsp.status_code} {rsp.text}")
    except Exception as e:
        logger.error(f"推送请求失败: {str(e)}")

@app.route("/")
def index():
    """触发推送（后台线程执行，不阻塞响应）"""
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-d2tz is running!", 200

def _push_real_data():
    """后台执行推送逻辑"""
    try:
        c, ct, n, nt = fetch_terror_info()
        logger.info(f"准备推送: 当前={c}, 即将={n}")
        if c or n:
            send_wecom_message(c, ct, n, nt)
        else:
            logger.warning("无有效数据，不推送")
    except Exception as e:
        logger.exception("后台推送失败")
        # 推送异常通知
        if WEBHOOK_URL:
            requests.post(
                WEBHOOK_URL,
                json={"msgtype": "text", "text": {"content": "后台异常▶请检查日志"}},
                timeout=5
            )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
