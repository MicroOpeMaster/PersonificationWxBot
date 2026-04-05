"""
企业微信群机器人 - 最稳定的方案

使用步骤:
1. 在企业微信群中添加机器人
2. 获取Webhook地址
3. 配置到 .env 文件: WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
4. 运行: python src/wecom_group_bot.py

特点:
- 官方支持，无封号风险
- 适合消息推送、定时提醒
- 只能发送消息，无法接收
"""
import os
import sys
import requests
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


class WeComGroupBot:
    """企业微信群机器人"""

    def __init__(self):
        self.webhook_url = os.getenv("WECOM_WEBHOOK_URL", "")
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.model = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

    def send_text(self, content: str) -> bool:
        """发送文本消息"""
        if not self.webhook_url:
            print("未配置 WECOM_WEBHOOK_URL")
            return False

        data = {
            "msgtype": "text",
            "text": {"content": content}
        }

        try:
            resp = requests.post(self.webhook_url, json=data, timeout=10)
            result = resp.json()
            if result.get("errcode") == 0:
                print(f"[发送成功] {content[:30]}...")
                return True
            else:
                print(f"[发送失败] {result}")
                return False
        except Exception as e:
            print(f"[发送异常] {e}")
            return False

    def chat_and_send(self, message: str) -> str:
        """AI回复并发送"""
        if not self.api_key:
            print("未配置 API Key")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": {"messages": [{"role": "user", "content": message}]},
            "parameters": {"temperature": 0.8, "max_tokens": 100}
        }

        try:
            resp = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers,
                json=payload,
                timeout=30
            )

            if resp.status_code == 200:
                result = resp.json()
                reply = result.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
                if reply:
                    self.send_text(f"AI回复: {reply}")
                    return reply
            else:
                print(f"API错误: {resp.status_code}")
                return None
        except Exception as e:
            print(f"API异常: {e}")
            return None


def main():
    print("=" * 50)
    print("企业微信群机器人")
    print("=" * 50)

    bot = WeComGroupBot()

    if not bot.webhook_url:
        print("\n请先配置 Webhook URL:")
        print("1. 在企业微信群中添加机器人")
        print("2. 复制 Webhook 地址")
        print("3. 添加到 .env: WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx")
        return

    print("\n输入消息发送，输入 'quit' 退出")

    while True:
        try:
            msg = input("\n> ").strip()
            if msg.lower() == 'quit':
                break
            if msg:
                bot.send_text(msg)
        except KeyboardInterrupt:
            break

    print("\n已退出")


if __name__ == "__main__":
    main()