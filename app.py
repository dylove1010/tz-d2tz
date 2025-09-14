import os, requests, logging, datetime
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

WEBHOOK_URL = "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644"
API_URL     = "https://www.d2tz.info/api/terror-zone"   # 公开接口（示例）

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app   = Flask(__name__)
sched = BackgroundScheduler()

def fetch_terror_info():
    """纯 requests 抓接口，无浏览器"""
    try:
        r = requests.get(API_URL, timeout=10)
        r.raise_for_status()
        data = r.json()
        # 假设返回 {"current":{"area":"xxx","time":"2025/06/19 08:00"},"next":{...}}
        current = data.get("current", {})
        next_   = data.get("next", {})
        return current.get("area"), current.get("time"), next_.get("area"), next_.get("time")
    except Exception as e:
        logger.warning("接口抓取失败: %s", e)
        return None, None, None, None

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
