import os
import requests
import logging
from flask import Flask
from threading import Thread

# 从环境变量读取配置（优先使用环境变量，兼容原代码的硬编码作为 fallback）
WEBHOOK_URL = os.environ.get("WEBHOOK_URL", "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=b0bcfe46-3aa1-4071-afd5-da63be5a8644")
# 直接使用数据接口，替代原网页URL
TARGET_API = "https://www.d2tz.info/api/online"

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)

def fetch_terror_info():
    """通过API获取恐怖地带数据，替代Selenium解析"""
    try:
        # 发起API请求（添加超时和请求头模拟浏览器）
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        }
        response = requests.get(TARGET_API, headers=headers, timeout=10)
        response.raise_for_status()  # 检查HTTP错误状态
        data = response.json()

        # 提取恐怖地带信息（过滤出terror为True的区域）
        terror_zones = [zone["name"] for zone in data.get("zones", []) if zone.get("terror")]
        
        # 按原逻辑返回当前和下一个区域（取前两个恐怖地带）
        current_area = terror_zones[0] if len(terror_zones) > 0 else None
        next_area = terror_zones[1] if len(terror_zones) > 1 else None
        
        # 原代码需要返回4个值（兼容send_wecom_message参数）
        return current_area, "", next_area, ""
    
    except Exception as e:
        logger.error("获取恐怖地带数据失败: %s", str(e))
        return None, None, None, None

def send_wecom_message(c, ct, n, nt):
    """发送企业微信消息（保持原格式）"""
    now = c or "暂无"
    soon = n or "暂无"
    content = f"{now}▶{soon}"  # 保持原分隔符格式
    try:
        rsp = requests.post(
            WEBHOOK_URL,
            json={"msgtype": "text", "text": {"content": content}},
            timeout=10
        )
        logger.info("企业微信推送结果: %s", rsp.json())
    except Exception as e:
        logger.error("企业微信推送失败: %s", str(e))

@app.route("/")
def index():
    """根路由触发推送（后台线程执行，不阻塞响应）"""
    Thread(target=_push_real_data, daemon=True).start()
    return "tz-d2tz is running!", 200

def _push_real_data():
    """实际执行数据抓取和推送的后台函数"""
    try:
        c, ct, n, nt = fetch_terror_info()
        if c or n:
            send_wecom_message(c, ct, n, nt)
        else:
            logger.warning("未获取到有效恐怖地带数据")
    except Exception as e:
        logger.exception("后台推送流程异常")
        # 异常时推送告警
        try:
            requests.post(
                WEBHOOK_URL,
                json={"msgtype": "text", "text": {"content": "后台异常▶后台异常"}},
                timeout=10
            )
        except Exception as push_err:
            logger.error("异常告警推送失败: %s", str(push_err))

if __name__ == "__main__":
    # 从环境变量获取端口（兼容Render部署）
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
