"""
Wechaty 微信机器人
跨平台支持 Linux/Mac/Windows
"""
import asyncio
import os
from dotenv import load_dotenv
from wechaty import Wechaty, Message, Contact, FileBox
from wechaty_puppet import PuppetOptions

load_dotenv()

# 引入百炼API
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.model_api import BailianAPI


class WechatyBot(Wechaty):
    """基于Wechaty的微信机器人"""

    def __init__(self, puppet_options: PuppetOptions = None):
        super().__init__(puppet_options)
        self.api = BailianAPI()
        self.auto_reply_enabled = True

        # 不回复的联系人列表
        self.exclude_contacts = ['文件传输助手', '微信团队', '公众平台']

    async def on_message(self, msg: Message):
        """消息处理回调"""
        try:
            # 获取消息信息
            contact = msg.talker()
            text = msg.text()
            msg_type = msg.type()

            # 过滤非文本消息
            if msg_type != "Message.Type.TEXT":
                return

            # 过滤自己发送的消息
            if msg.self():
                return

            # 过滤排除的联系人
            if contact.name in self.exclude_contacts:
                return

            # 过滤群消息（可选）
            if msg.room():
                return

            print(f"[收到消息] {contact.name}: {text}")

            # 获取AI回复
            reply = self.api.chat(text, temperature=0.8, max_tokens=100)

            if reply and self.auto_reply_enabled:
                print(f"[发送回复] -> {contact.name}: {reply[:50]}...")
                await msg.say(reply)

        except Exception as e:
            print(f"处理消息异常: {e}")

    async def on_login(self, contact: Contact):
        """登录回调"""
        print(f"[登录成功] {contact.name}")
        print("机器人已启动，等待消息...")

    async def on_logout(self, contact: Contact):
        """退出回调"""
        print(f"[退出登录] {contact.name}")

    async def on_scan(self, status, qrcode_url):
        """扫码回调"""
        print(f"[扫码状态] {status}")
        print(f"请扫码登录: {qrcode_url}")


async def main():
    """启动机器人"""
    # 配置puppet
    # Wechaty需要配置puppet token
    # 免费方案: 使用wechat4u (Web微信，风险较高)
    # 推荐方案: 使用padlocal或其他付费puppet

    puppet_token = os.getenv("WECHATY_PUPPET_TOKEN", "")

    if puppet_token:
        puppet_options = PuppetOptions(
            puppet="wechaty-puppet-service",
            token=puppet_token
        )
    else:
        # 使用免费puppet (Web微信)
        puppet_options = PuppetOptions(
            puppet="wechaty-puppet-wechat4u"
        )

    bot = WechatyBot(puppet_options)

    print("=" * 50)
    print("Wechaty 微信机器人启动")
    print("=" * 50)
    print("\n请扫码登录微信...")

    await bot.start()


def run():
    """运行入口"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n机器人已停止")


if __name__ == "__main__":
    run()