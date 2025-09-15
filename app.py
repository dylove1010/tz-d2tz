import os, requests, logging
from flask import Flask
from bs4 import BeautifulSoup
from threading import Thread

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL  = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    """直接 requests 抓取页面 + BeautifulSoup 解析"""
    resp = requests.get(TARGET_URL, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    rows = soup.select("tbody[role='rowgroup'] tr")[:2]
    out = []
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            time_text = cells[0].get_text(strip=True)
            area_raw  = cells[1].get_text(strip=True)
            # 去掉 "▶" 前缀
            area_only = area_raw.split("▶")[-1]
            out.append((time_text, area_only))

    if len(out) < 2:
        return None, None, None, None

    # 网站是最新在上面：第 0 行是【下一个】，第 1 行是【当前】
    next_time, next_area = out[0]
    current_time, current_area = out[1]
    return current_area, current_time, next_area, next_time

def send_wecom_message(c, ct, n, nt):
    now  = c or "暂无"
    soon = n or "暂无"
    content = f"{now}▶{soon}"
    rsp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=5)
    logger.info("WeCom response: %s", rsp.json())

@app.route("/")
def index():
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-bot is running!", 200

def _push_real_data():
    try:
        c, ct, n, nt = fetch_terror_info()
        if c or n:
            send_wecom_message(c, ct, n, nt)
        else:
            requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": "抓取失败"}}, timeout=5)
    except Exception as e:
        logger.exception("抓取失败")
        requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": "后台▶后台"}}, timeout=5)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
