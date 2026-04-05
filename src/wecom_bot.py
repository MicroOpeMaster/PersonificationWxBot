"""
企业微信群机器人 - 最稳定的微信消息推送方案

优势:
- 官方支持，无封号风险
- Linux/Windows 都可用
- 免费使用

使用步骤:
1. 打开企业微信手机App
2. 进入任意群聊 -> 群设置 -> 群机器人 -> 添加
3. 复制 Webhook 地址
4. 配置到 .env: WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

运行: python src/wecom_bot.py
"""
import os
import sys
import requests
import json
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


class WeComBot:
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
                print(f"[发送成功] {content[:50]}")
                return True
            else:
                print(f"[发送失败] {result}")
                return False
        except Exception as e:
            print(f"[发送异常] {e}")
            return False

    def send_markdown(self, content: str) -> bool:
        """发送Markdown消息"""
        if not self.webhook_url:
            return False

        data = {
            "msgtype": "markdown",
            "markdown": {"content": content}
        }

        try:
            resp = requests.post(self.webhook_url, json=data, timeout=10)
            return resp.json().get("errcode") == 0
        except:
            return False

    def chat(self, message: str) -> str:
        """调用百炼API"""
        if not self.api_key:
            return "未配置API Key"

        try:
            resp = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "input": {"messages": [{"role": "user", "content": message}]},
                    "parameters": {"temperature": 0.8, "max_tokens": 200}
                },
                timeout=30
            )

            if resp.status_code == 200:
                data = resp.json()
                return data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"API异常: {e}")

        return None

    def chat_and_send(self, message: str):
        """AI对话并发送回复"""
        reply = self.chat(message)
        if reply:
            self.send_markdown(f"**用户**: {message}\n\n**AI**: {reply}")
            return reply
        return None


def test_send():
    """测试发送消息"""
    bot = WeComBot()

    if not bot.webhook_url:
        print("=" * 50)
        print("请先配置企业微信群机器人")
        print("=" * 50)
        print("\n步骤:")
        print("1. 打开企业微信App")
        print("2. 进入群聊 -> 群设置 -> 群机器人 -> 添加")
        print("3. 复制Webhook地址")
        print("4. 添加到 .env 文件:")
        print("   WECOM_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx")
        return

    print("发送测试消息...")
    bot.send_text("机器人测试成功!")

    print("\n测试AI对话...")
    bot.chat_and_send("你好")


def interactive():
    """交互模式"""
    bot = WeComBot()

    if not bot.webhook_url:
        print("请先配置 WECOM_WEBHOOK_URL")
        return

    print("=" * 50)
    print("企业微信机器人 - 交互模式")
    print("=" * 50)
    print("输入消息发送到群，输入 'quit' 退出\n")

    while True:
        try:
            msg = input("> ").strip()
            if msg.lower() == 'quit':
                break
            if msg:
                bot.chat_and_send(msg)
        except KeyboardInterrupt:
            break

    print("\n已退出")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="测试发送")
    parser.add_argument("-i", "--interactive", action="store_true", help="交互模式")
    args = parser.parse_args()

    if args.test:
        test_send()
    elif args.interactive:
        interactive()
    else:
        test_send()