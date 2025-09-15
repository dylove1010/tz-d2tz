import os
import requests
import logging
from flask import Flask
from bs4 import BeautifulSoup
from threading import Thread

# ---------- 配置 ----------
WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
TARGET_URL = "https://www.d2tz.info/?l=zh-cn"
TIMEOUT = 10  # 请求超时

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# ---------- 抓取逻辑 ----------
def fetch_terror_info():
    try:
        resp = requests.get(TARGET_URL, timeout=TIMEOUT)
        resp.raise_for_status()
        html = resp.text
        logger.info("页面获取成功，长度=%d", len(html))

        soup = BeautifulSoup(html, "html.parser")
        rows = soup.select("tbody[role='rowgroup'] tr")[:2]  # 取前两行
        if not rows or len(rows) < 2:
            return None, None, None, None

        def parse_row(row):
            cells = row.find_all("td")
            if len(cells) >= 2:
                time_text = cells[0].get_text(strip=True)
                area_text = cells[1].get_text(strip=True)
                # 去掉 Coming soon / Now 字样
                for kw in ["Coming soon", "Now"]:
                    area_text = area_text.replace(kw, "").strip()
                return time_text, area_text
            return None, None

        # 网站最新时间在前，第一条是下一个（即即将生效），第二条是当前
        next_time, next_area = parse_row(rows[0])
        current_time, current_area = parse_row(rows[1])

        return current_area, current_time, next_area, next_time
    except Exception as e:
        logger.warning("抓取失败: %s", e)
        return None, None, None, None

# ---------- 推送逻辑 ----------
def send_wecom_message(current, current_time, next_, next_time):
    current_str = f"{current_time or '信息未抓取到'} 【{current or '信息未抓取到'}】"
    next_str = f"{next_time or '信息未抓取到'} 【{next_ or '信息未抓取到'}】"
    content = f"当前恐怖地带: {current_str}\n下一个恐怖地带: {next_str}"
    try:
        resp = requests.post(WEBHOOK_URL, json={"msgtype": "text", "text": {"content": content}}, timeout=5)
        logger.info("WeCom response: %s", resp.json())
    except Exception as e:
        logger.warning("推送失败: %s", e)

# ---------- 后台线程推送 ----------
def _push_real_data():
    c, ct, n, nt = fetch_terror_info()
    if c or n:
        send_wecom_message(c, ct, n, nt)
    else:
        # 抓取失败占位
        send_wecom_message("未获取到信息", "", "未获取到信息", "")

# ---------- Flask 路由 ----------
@app.route("/")
def index():
    # 异步后台推送，不阻塞 Render 健康检查
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-bot is running!", 200

@app.route("/test")
def test_push():
    Thread(target=_push_real_data, daemon=True).start()
    return "手动测试推送触发", 200

# ---------- 启动 ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
