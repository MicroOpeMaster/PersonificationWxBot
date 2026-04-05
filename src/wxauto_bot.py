"""
wxauto 微信机器人 - 修复版
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


def find_wechat_window():
    """查找微信窗口句柄"""
    result = [None]

    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        # 微信窗口标题通常是"微信"或包含"WeChat"
        if title == '微信' or title == 'WeChat' or '微信' in title:
            result[0] = hwnd
        return True

    win32gui.EnumWindows(callback, None)
    return result[0]


def show_wechat():
    """显示并激活微信窗口"""
    hwnd = find_wechat_window()
    if hwnd:
        # 显示窗口
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        # 激活窗口
        win32gui.SetForegroundWindow(hwnd)
        return True
    return False


class WxAutoBot:
    """wxauto微信机器人"""

    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.model = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")
        self.wx = None

    def init_wechat(self):
        """初始化微信连接"""
        print("正在查找微信窗口...")

        hwnd = find_wechat_window()
        if not hwnd:
            print("\n未找到微信窗口!")
            print("请确保:")
            print("  1. 微信PC客户端已打开")
            print("  2. 已登录账号")
            print("  3. 微信窗口没有被最小化")
            return False

        print(f"找到微信窗口: {hwnd}")

        # 显示微信窗口
        print("正在激活微信窗口...")
        show_wechat()
        time.sleep(1)

        # 尝试导入wxauto
        try:
            from wxauto import WeChat
            self.wx = WeChat()
            print("微信连接成功!")
            return True
        except Exception as e:
            print(f"连接失败: {e}")

            # 尝试其他方式
            try:
                # 不自动显示窗口
                from wxauto import WeChat
                self.wx = WeChat(debug=True)
                print("使用debug模式连接成功!")
                return True
            except Exception as e2:
                print(f"仍然失败: {e2}")
                return False

    def chat(self, message: str) -> str:
        """调用百炼API"""
        if not self.api_key:
            return None

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
                    "parameters": {"temperature": 0.8, "max_tokens": 100}
                },
                timeout=30
            )

            if resp.status_code == 200:
                data = resp.json()
                return data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
        except Exception as e:
            print(f"API异常: {e}")

        return None

    def send_to(self, who: str, message: str):
        """发送消息给指定联系人"""
        if not self.wx:
            print("微信未连接")
            return False

        try:
            self.wx.SendMsg(message, who)
            print(f"[发送成功] -> {who}")
            return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False

    def test_send(self):
        """测试发送消息"""
        print("\n测试发送消息到文件传输助手...")
        return self.send_to("文件传输助手", "测试消息")

    def interactive(self):
        """交互模式 - 手动输入发送"""
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
                    # 先调用AI
                    print("AI思考中...")
                    reply = self.chat(msg)
                    if reply:
                        print(f"AI: {reply[:50]}...")
                        self.send_to(who, reply)
                    else:
                        self.send_to(who, msg)

            except KeyboardInterrupt:
                break

        print("\n已退出")


def main():
    print("=" * 50)
    print("wxauto 微信机器人")
    print("=" * 50)

    # 检查微信窗口
    hwnd = find_wechat_window()
    if hwnd:
        print(f"\n检测到微信窗口: {hwnd}")
    else:
        print("\n未检测到微信窗口!")
        print("请先打开微信PC客户端并登录")
        return

    bot = WxAutoBot()

    if not bot.init_wechat():
        print("\n初始化失败，请尝试:")
        print("  1. 以管理员身份运行")
        print("  2. 确保微信窗口可见（未最小化）")
        print("  3. 关闭其他可能干扰的程序")
        return

    # 进入交互模式
    bot.interactive()


if __name__ == "__main__":
    main()