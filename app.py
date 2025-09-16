import os
import requests
import logging
from flask import Flask
from threading import Thread

# 从环境变量读取企业微信机器人地址（部署时需配置）
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "")
# 数据接口（直接获取JSON数据）
TARGET_API = "https://www.d2tz.info/api/online"

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

# 健康检查接口（解决Render部署超时）
@app.route("/health")
def health_check():
    return "OK", 200

# 根路由触发推送
@app.route("/")
def index():
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-d2tz is running!", 200

def fetch_terror_info():
    """通过API获取恐怖地带数据"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(TARGET_API, headers=headers, timeout=10)
        response.raise_for_status()  # 检查请求是否成功
        data = response.json()

        # 提取恐怖地带（terror为True的区域）
        terror_zones = [zone["name"] for zone in data.get("zones", []) if zone.get("terror")]
        
        # 取前两个区域（当前和下一个）
        current_area = terror_zones[0] if len(terror_zones) > 0 else None
        next_area = terror_zones[1] if len(terror_zones) > 1 else None
        
        return current_area, "", next_area, ""  # 保持原返回格式
    except Exception as e:
        logger.error("获取数据失败: %s", str(e))
        return None, None, None, None

def send_wecom_message(c, ct, n, nt):
    """发送企业微信消息"""
    now = c or "暂无"
    soon = n or "暂无"
    content = f"{now}▶{soon}"
    try:
        if not WEBHOOK_URL:
            logger.error("未配置WEBHOOK_URL，请检查环境变量")
            return
        rsp = requests.post(
            WEBHOOK_URL,
            json={"msgtype": "text", "text": {"content": content}},
            timeout=10
        )
        logger.info("推送结果: %s", rsp.json())
    except Exception as e:
        logger.error("推送失败: %s", str(e))

def _push_real_data():
    """后台执行推送逻辑"""
    try:
        c, ct, n, nt = fetch_terror_info()
        if c or n:
            send_wecom_message(c, ct, n, nt)
        else:
            logger.warning("未获取到有效数据")
    except Exception as e:
        logger.exception("后台推送异常")
        # 异常时推送告警
        if WEBHOOK_URL:
            try:
                requests.post(
                    WEBHOOK_URL,
                    json={"msgtype": "text", "text": {"content": "后台异常▶后台异常"}},
                    timeout=10
                )
            except Exception as err:
                logger.error("异常告警推送失败: %s", str(err))

if __name__ == "__main__":
    # 使用Render分配的端口（必填）
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
