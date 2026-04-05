"""
微信机器人 - 基于wxauto实现消息监听和自动回复
"""
import os
import sys
import time
import ctypes

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

import requests
import win32gui
import win32con
import win32process


def find_wechat_window():
    """查找微信窗口句柄"""
    result = []

    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        if title == '微信' or 'WeChat' in title:
            result.append(hwnd)
        return True

    win32gui.EnumWindows(callback, None)
    return result


def activate_window(hwnd):
    """激活窗口"""
    # 先显示窗口
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    time.sleep(0.3)
    # 设置前台窗口
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception as e:
        # 如果SetForegroundWindow失败，尝试其他方法
        # 模拟按键激活
        ctypes.windll.user32.keybd_event(0, 0, 0, 0)
        time.sleep(0.1)
        win32gui.SetForegroundWindow(hwnd)


class WechatBot:
    """微信自动回复机器人"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.model = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")
        self.wx = None
        self.listen_list = []  # 监听的聊天列表

    def chat_with_ai(self, message: str) -> str:
        """调用百炼API获取回复"""
        if not self.api_key:
            return "未配置API Key"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": {"messages": [{"role": "user", "content": message}]},
            "parameters": {"temperature": 0.8, "max_tokens": 150}
        }

        try:
            resp = requests.post(
                "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                headers=headers, json=payload, timeout=30
            )
            if resp.status_code == 200:
                result = resp.json()
                return result.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"API异常: {e}")
        return None

    def init_wechat(self):
        """初始化微信连接"""
        print("查找微信窗口...")
        windows = find_wechat_window()

        if not windows:
            print("未找到微信窗口！请确保微信PC客户端已打开并登录")
            return False

        print(f"找到 {len(windows)} 个微信窗口")

        # 激活第一个窗口
        hwnd = windows[0]
        print(f"激活窗口: {hwnd}")
        activate_window(hwnd)
        time.sleep(1)

        # 尝试多次连接
        for attempt in range(3):
            try:
                from wxauto import WeChat
                print(f"尝试连接 ({attempt + 1}/3)...")
                self.wx = WeChat()
                print("连接成功!")
                return True
            except Exception as e:
                print(f"连接失败: {e}")
                if attempt < 2:
                    time.sleep(2)
                    activate_window(hwnd)

        return False

    def add_listen_chat(self, who: str):
        """添加要监听的聊天"""
        if self.wx:
            try:
                self.wx.AddListenChat(who)
                self.listen_list.append(who)
                print(f"已添加监听: {who}")
            except Exception as e:
                print(f"添加监听失败: {e}")

    def send_message(self, who: str, message: str):
        """发送消息"""
        if self.wx:
            try:
                self.wx.SendMsg(message, who)
                print(f"[发送] -> {who}: {message[:30]}...")
                return True
            except Exception as e:
                print(f"发送失败: {e}")
        return False

    def run(self, listen_targets=None):
        """运行机器人"""
        if not self.init_wechat():
            return

        # 默认监听文件传输助手用于测试
        targets = listen_targets or ["文件传输助手"]

        for target in targets:
            self.add_listen_chat(target)

        print("\n" + "=" * 50)
        print("机器人运行中...")
        print("=" * 50)
        print("监听聊天:", targets)
        print("按 Ctrl+C 退出\n")

        # 消息处理循环
        try:
            while True:
                # 获取新消息
                msgs = self.wx.GetListenMessage()

                for chat, messages in msgs.items():
                    for msg in messages:
                        # msg[0] 是发送者, msg[1] 是内容, msg[2] 是消息类型
                        sender = msg[0]
                        content = msg[1]
                        msg_type = msg[2] if len(msg) > 2 else 'text'

                        # 过滤自己发送的消息
                        if sender == 'self':
                            continue

                        print(f"\n[收到] {chat}/{sender}: {content[:50]}...")

                        # 只处理文本消息
                        if msg_type != 'text':
                            continue

                        # 过滤太短的消息
                        if len(content.strip()) < 2:
                            continue

                        # AI回复
                        print("AI思考中...")
                        reply = self.chat_with_ai(content)

                        if reply:
                            print(f"[回复] {reply[:50]}...")
                            self.send_message(chat, reply)

                time.sleep(1)  # 降低轮询频率

        except KeyboardInterrupt:
            print("\n机器人已停止")

    def test_send(self):
        """测试发送功能"""
        if not self.init_wechat():
            return

        print("\n测试发送消息到文件传输助手...")
        self.send_message("文件传输助手", "你好，这是微信机器人测试消息！")

    def interactive(self):
        """交互模式"""
        if not self.init_wechat():
            return

        print("\n" + "=" * 50)
        print("交互模式")
        print("=" * 50)
        print("格式: 联系人:消息内容")
        print("例如: 文件传输助手:你好")
        print("输入 'quit' 退出\n")

        while True:
            try:
                inp = input("> ").strip()
                if inp.lower() == 'quit':
                    break

                if ':' not in inp:
                    print("格式错误，请用: 联系人:消息")
                    continue

                who, msg = inp.split(':', 1)
                who = who.strip()
                msg = msg.strip()

                if who and msg:
                    # AI回复
                    print("AI思考中...")
                    reply = self.chat_with_ai(msg)
                    if reply:
                        print(f"AI: {reply[:60]}...")
                        self.send_message(who, reply)
                    else:
                        self.send_message(who, msg)

            except KeyboardInterrupt:
                break

        print("\n已退出")


def main():
    print("=" * 50)
    print("微信自动回复机器人")
    print("=" * 50)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="运行自动回复模式")
    parser.add_argument("--test", action="store_true", help="测试发送功能")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--listen", nargs='+', help="监听的联系人列表")
    args = parser.parse_args()

    bot = WechatBot()

    if args.test:
        bot.test_send()
    elif args.interactive:
        bot.interactive()
    elif args.run:
        bot.run(args.listen)
    else:
        # 默认运行模式
        print("\n用法:")
        print("  python run_bot.py --run          # 自动回复模式")
        print("  python run_bot.py --test         # 测试发送")
        print("  python run_bot.py --interactive  # 交互模式")
        print("  python run_bot.py --run --listen 联系人1 联系人2")


if __name__ == "__main__":
    main()