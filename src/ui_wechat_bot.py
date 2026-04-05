"""
基于UI自动化的微信机器人
使用 pyautogui + pyperclip 实现消息发送
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import pyautogui
import pyperclip
from dotenv import load_dotenv

load_dotenv()

from src.model_api import BailianAPI

# 安全设置：防止鼠标失控
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.5


class UIWeChatBot:
    """基于UI自动化的微信机器人"""

    def __init__(self, api: BailianAPI):
        self.api = api
        self.running = False

        # 微信快捷键
        self.wechat_hotkey = ['ctrl', 'alt', 'w']  # 激活微信
        self.search_hotkey = ['ctrl', 'f']  # 搜索联系人
        self.send_hotkey = ['enter']  # 发送消息

    def activate_wechat(self):
        """激活微信窗口"""
        try:
            # 尝试使用快捷键激活微信
            pyautogui.hotkey(*self.wechat_hotkey)
            time.sleep(1)
            return True
        except Exception as e:
            print(f"激活微信失败: {e}")
            return False

    def send_message(self, contact_name: str, message: str):
        """
        发送消息给指定联系人

        Args:
            contact_name: 联系人名称（备注名或昵称）
            message: 要发送的消息
        """
        try:
            # 激活微信
            self.activate_wechat()

            # 搜索联系人
            pyautogui.hotkey(*self.search_hotkey)
            time.sleep(0.5)

            # 输入联系人名称
            pyperclip.copy(contact_name)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)

            # 点击搜索结果（按Enter选中第一个结果）
            pyautogui.press('enter')
            time.sleep(0.5)

            # 清空搜索框，准备输入消息
            pyautogui.press('esc')
            time.sleep(0.3)

            # 输入消息
            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)

            # 发送消息
            pyautogui.press('enter')

            print(f"[发送成功] -> {contact_name}: {message[:30]}...")
            return True

        except Exception as e:
            print(f"发送失败: {e}")
            return False

    def get_reply(self, message: str) -> str:
        """获取AI回复"""
        reply = self.api.chat(message, temperature=0.8, max_tokens=100)
        return reply if reply else ""

    def reply_to_contact(self, contact_name: str, user_message: str):
        """
        回复指定联系人的消息

        Args:
            contact_name: 联系人名称
            user_message: 用户发来的消息内容
        """
        # 获取AI回复
        reply = self.get_reply(user_message)

        if reply:
            # 发送回复
            self.send_message(contact_name, reply)
        else:
            print("[警告] API未返回回复")


def test_send():
    """测试发送消息功能"""
    print("=" * 50)
    print("微信机器人测试 - 发送消息")
    print("=" * 50)

    api = BailianAPI()
    bot = UIWeChatBot(api)

    # 测试发送
    test_contact = "文件传输助手"  # 安全的测试目标
    test_message = "你好，这是机器人测试消息"

    print(f"\n发送测试消息给: {test_contact}")
    success = bot.send_message(test_contact, test_message)

    if success:
        print("\n测试成功！消息已发送")
    else:
        print("\n测试失败")


def interactive_mode():
    """交互模式：手动输入消息发送"""
    print("=" * 50)
    print("微信机器人 - 交互模式")
    print("=" * 50)

    api = BailianAPI()
    bot = UIWeChatBot(api)

    print("\n输入联系人名称和消息，机器人会自动发送")
    print("格式: 联系人名称:消息内容")
    print("输入 'quit' 退出")

    while True:
        try:
            input_str = input("\n> ").strip()

            if input_str.lower() == 'quit':
                print("退出交互模式")
                break

            if ':' not in input_str:
                print("格式错误，请使用: 联系人名称:消息内容")
                continue

            contact, message = input_str.split(':', 1)
            contact = contact.strip()
            message = message.strip()

            if not contact or not message:
                print("联系人和消息不能为空")
                continue

            # 发送消息
            bot.send_message(contact, message)

        except KeyboardInterrupt:
            print("\n退出")
            break
        except Exception as e:
            print(f"错误: {e}")


def ai_reply_mode(contact_name: str):
    """
    AI回复模式：输入用户消息，AI生成回复并发送

    Args:
        contact_name: 要回复的联系人名称
    """
    print("=" * 50)
    print("微信机器人 - AI回复模式")
    print("=" * 50)
    print(f"目标联系人: {contact_name}")
    print("\n输入用户发来的消息，AI会生成回复并发送")
    print("输入 'quit' 退出")

    api = BailianAPI()
    bot = UIWeChatBot(api)

    while True:
        try:
            user_message = input("\n用户消息: ").strip()

            if user_message.lower() == 'quit':
                print("退出")
                break

            if not user_message:
                continue

            # AI生成回复并发送
            bot.reply_to_contact(contact_name, user_message)

        except KeyboardInterrupt:
            print("\n退出")
            break


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="微信机器人")
    parser.add_argument("--test", action="store_true", help="测试发送消息")
    parser.add_argument("--interactive", action="store_true", help="交互发送模式")
    parser.add_argument("--ai-reply", type=str, help="AI回复模式，指定联系人名称")

    args = parser.parse_args()

    if args.test:
        test_send()
    elif args.interactive:
        interactive_mode()
    elif args.ai_reply:
        ai_reply_mode(args.ai_reply)
    else:
        print("请指定运行模式:")
        print("  --test          测试发送消息")
        print("  --interactive   交互发送模式")
        print("  --ai-reply 联系人名称  AI回复模式")