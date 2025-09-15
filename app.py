import os
import logging
import requests
from flask import Flask
from bs4 import BeautifulSoup
from threading import Thread

# ====== 配置 ======
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=替换成你的key")
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

# ====== 日志 ======
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# ====== Flask 应用 ======
app = Flask(__name__)

def fetch_terror_info():
    """直接请求网页并解析，避免用 Selenium"""
    resp = requests.get(TARGET_URL, timeout=10, headers={
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36"
    })
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")
    rows = soup.select("tbody[role='rowgroup'] tr")[:2]

    out = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            time_text = cells[0].get_text(strip=True)
            area_text = cells[1].get_text(strip=True)
            # 去掉 "Now▶" / "Coming soon▶"
            area_text = area_text.replace("Now", "").replace("Coming soon", "").replace("▶", "").strip()
            out.append((time_text, area_text))

    if len(out) < 2:
        return None, None, None, None

    # 网站是「最新在上」，所以第 1 行是下一个，第 2 行是当前
    next_time, next_area = out[0]
    current_time, current_area = out[1]
    return current_area, current_time, next_area, next_time

def send_wecom_message(c, ct, n, nt):
    """推送到企业微信群"""
    msg = f"{ct} 【{c or '暂无'}】\n{nt} 【{n or '暂无'}】"
    rsp = requests.post(WEBHOOK_URL, json={
        "msgtype": "text",
        "text": {"content": msg}
    }, timeout=5)
    logger.info("WeCom response: %s", rsp.json())

@app.route("/")
def index():
    # 用线程异步推送，不阻塞 Render 的健康检查
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-bot running!", 200

def _push_real_data():
    try:
        c, ct, n, nt = fetch_terror_info()
        if c or n:
            send_wecom_message(c, ct, n, nt)
    except Exception as e:
        logger.error("抓取失败: %s", e)
        requests.post(WEBHOOK_URL, json={
            "msgtype": "text",
            "text": {"content": "后台▶后台"}
        }, timeout=5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
