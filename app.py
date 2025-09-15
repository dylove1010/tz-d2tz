import os
import requests
import logging
from flask import Flask
from bs4 import BeautifulSoup
from threading import Thread

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL = "https://www.d2tz.info/?l=zh-cn"

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    """抓取当前和下一个恐怖地带信息"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/122.0.0.0 Safari/537.36"
        }
        resp = requests.get(TARGET_URL, headers=headers, timeout=10)
        resp.raise_for_status()
        logger.info("页面获取成功，长度=%s", len(resp.text))
        logger.info("前500字符:\n%s", resp.text[:500])

        soup = BeautifulSoup(resp.text, "html.parser")
        rows = soup.select("tbody[role='rowgroup'] tr")[:2]

        out = []
        for row in rows:
            cells = row.select("td")
            if len(cells) >= 2:
                area_raw = cells[1].get_text(strip=True)
                # 去掉 "Now" / "Coming soon" 等字样
                area_only = area_raw.split("▶")[-1]
                out.append((cells[0].get_text(strip=True), area_only))

        if len(out) < 2:
            return None, None, None, None

        # 注意顺序：最新的在前面，所以第1条是下一个，第2条是当前
        next_time, next_area = out[0]
        current_time, current_area = out[1]
        return current_area, current_time, next_area, next_time
    except Exception as e:
        logger.exception("fetch_terror_info 出错")
        return None, None, None, None

def send_wecom_message(current, current_time, next_, next_time):
    """推送文字消息到企业微信"""
    current_time_fmt = current_time or "信息未抓取到"
    next_time_fmt = next_time or "信息未抓取到"
    current_area_fmt = current or "信息未抓取到"
    next_area_fmt = next_ or "信息未抓取到"

    content = (f"当前恐怖地带开始时间: {current_time_fmt}\n"
               f"当前恐怖地带: 【{current_area_fmt}】\n"
               f"下一个恐怖地带开始时间: {next_time_fmt}\n"
               f"下一个恐怖地带: 【{next_area_fmt}】")
    try:
        rsp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=5)
        logger.info("WeCom response: %s", rsp.json())
    except Exception as e:
        logger.exception("推送企业微信失败")

def push_job():
    try:
        current, current_time, next_, next_time = fetch_terror_info()
        send_wecom_message(current, current_time, next_, next_time)
    except Exception:
        # 如果抓取失败，推送占位信息
        requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": "后台▶后台"}}, timeout=5)

# ---------- 根路由 ---------- 
@app.route("/")
def index():
    # 后台线程推送，不阻塞 Render 检测
    Thread(target=push_job, daemon=True).start()
    return "tz-bot is running!", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
