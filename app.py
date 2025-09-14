import os, requests, logging
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# ========== 配置 ==========
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"
WAIT_TIME   = 10
# ==========================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app   = Flask(__name__)
sched = BackgroundScheduler()

def fetch_terror_info():
    """Selenium 抓取当前 & 下一个恐怖地带"""
    options = Options()
    options.binary_location = "/usr/bin/chromium-driver"   # 系统驱动
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--single-process")               # 省内存
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(TARGET_URL)
        # 等待表格渲染
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        WebDriverWait(driver, WAIT_TIME).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "tbody[role='rowgroup'] tr"))
        )
        rows = driver.find_elements(By.CSS_SELECTOR, "tbody[role='rowgroup'] tr")
        out = []
        for row in rows[:2]:
            cells = row.find_elements(By.TAG_NAME, "td")
            if len(cells) >= 2:
                time_text = cells[0].text.strip()
                area_text = cells[1].text.strip()
                out.append((time_text, area_text))
        if len(out) < 2:
            return None, None, None, None
        next_time, next_area = out[0]
        current_time, current_area = out[1]
        return current_area, current_time, next_area, next_time
    except Exception as e:
        logger.warning("抓取失败: %s", e)
        return None, None, None, None
    finally:
        driver.quit()

def send_wecom_message(c, ct, n, nt):
    ct_fmt = ct.replace("2025/", "") if ct else "信息未抓取到"
    nt_fmt = nt.replace("2025/", "") if nt else "信息未抓取到"
    content = (f"当前恐怖地带开始时间: {ct_fmt}\n"
               f"当前恐怖地带: 【{c or '信息未抓取到'}】\n"
               f"下一个恐怖地带开始时间: {nt_fmt}\n"
               f"下一个恐怖地带: 【{n or '信息未抓取到'}】")
    rsp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}})
    logger.info("WeCom response: %s", rsp.json())

def main_job():
    logger.info("Scheduled task triggered")
    c, ct, n, nt = fetch_terror_info()
    send_wecom_message(c, ct, n, nt)
    logger.info("Scheduled task completed")

# 定时任务：每小时 1 次
sched.add_job(main_job, "interval", hours=1, id="tz_job")
sched.start()

@app.route("/")
def index():
    return "tz-bot is running!", 200

@app.route("/test")
def test():
    main_job()
    return "manual push done", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
