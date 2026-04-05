"""
微信机器人 - 基于键盘快捷键实现
通过微信快捷键操作实现消息监听和自动回复
适用于新版微信客户端

运行前请:
1. 打开微信PC客户端并登录
2. 打开要监听的聊天窗口（如文件传输助手）
3. 运行此脚本

运行: python simple_bot.py
"""
import os
import sys
import time
import requests
import pyautogui
import pyperclip
import win32gui
import win32con

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))


# ========== 配置 ===========
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

# 对话历史
chat_history = {}
MAX_HISTORY = 10


def chat_with_ai(message: str, sender: str = "") -> str:
    """调用阿里云百炼API"""
    if not API_KEY:
        return "API Key未配置"

    history = chat_history.get(sender, [])
    messages = history.copy()
    messages.append({"role": "user", "content": message})

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "input": {"messages": messages},
        "parameters": {
            "temperature": 0.85,
            "max_tokens": 200,
            "result_format": "message",
            "enable_thinking": False
        }
    }

    try:
        resp = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers=headers, json=payload, timeout=30
        )
        if resp.status_code == 200:
            result = resp.json()
            reply = result.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")

            if sender:
                if sender not in chat_history:
                    chat_history[sender] = []
                chat_history[sender].append({"role": "user", "content": message})
                chat_history[sender].append({"role": "assistant", "content": reply})
                if len(chat_history[sender]) > MAX_HISTORY * 2:
                    chat_history[sender] = chat_history[sender][-MAX_HISTORY * 2:]

            return reply
    except Exception as e:
        print(f"[API异常] {e}")

    return None


def find_wechat():
    """查找微信窗口"""
    result = [None]
    def callback(hwnd, _):
        try:
            cls = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)
            if cls == 'Qt51514QWindowIcon' or (title and '微信' in title):
                result[0] = hwnd
        except:
            pass
        return True
    win32gui.EnumWindows(callback, None)
    return result[0]


def activate_wechat(hwnd):
    """激活微信窗口"""
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
        win32gui.SetForegroundWindow(hwnd)
        time.sleep(0.5)


def send_message(message: str):
    """发送消息（通过剪贴板）"""
    # 复制到剪贴板
    pyperclip.copy(message)
    time.sleep(0.1)
    # 粘贴
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.2)
    # 发送
    pyautogui.press('enter')


def switch_to_chat(name: str):
    """切换到指定聊天"""
    # 搜索联系人
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(0.3)
    pyperclip.copy(name)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('esc')


class SimpleWechatBot:
    """简单微信机器人"""

    def __init__(self):
        self.hwnd = None
        self.running = False
        self.last_clipboard = ""
        self.monitor_chat = "文件传输助手"  # 默认监听的聊天

    def init(self):
        """初始化"""
        print("查找微信窗口...")
        self.hwnd = find_wechat()

        if not self.hwnd:
            print("未找到微信窗口！请确保微信PC客户端已打开并登录")
            return False

        print(f"找到微信窗口: {self.hwnd}")
        activate_wechat(self.hwnd)
        return True

    def run_interactive(self):
        """交互模式 - 手动输入发送"""
        if not self.init():
            return

        print("\n" + "=" * 50)
        print("交互模式")
        print("=" * 50)
        print("输入消息，机器人会AI回复并发送到当前聊天窗口")
        print("输入 'quit' 退出")
        print("=" * 50)

        while True:
            try:
                msg = input("\n输入消息: ").strip()
                if msg.lower() == 'quit':
                    break

                if not msg:
                    continue

                # AI回复
                print("AI思考中...")
                reply = chat_with_ai(msg, "current")

                if reply:
                    print(f"AI回复: {reply[:80]}...")
                    # 激活微信
                    activate_wechat(self.hwnd)
                    time.sleep(0.3)
                    # 发送
                    send_message(reply)
                    print("已发送!")
                else:
                    print("AI未返回回复")

            except KeyboardInterrupt:
                break

        print("\n已退出")

    def test_send(self):
        """测试发送"""
        if not self.init():
            return

        print("\n测试发送消息到文件传输助手...")

        # 切换到文件传输助手
        switch_to_chat("文件传输助手")
        time.sleep(1)

        # 发送测试消息
        send_message("你好，这是微信机器人测试消息！")
        print("测试消息已发送！")

    def auto_reply_mode(self, target_chat: str = "文件传输助手"):
        """自动回复模式 - 监听剪贴板变化"""
        if not self.init():
            return

        self.monitor_chat = target_chat
        self.running = True

        # 切换到目标聊天
        print(f"\n切换到: {target_chat}")
        switch_to_chat(target_chat)
        time.sleep(1)

        print("\n" + "=" * 50)
        print("自动回复模式")
        print("=" * 50)
        print(f"监听聊天: {target_chat}")
        print("=" * 50)
        print("使用方法:")
        print("  1. 收到消息后，复制消息内容到剪贴板")
        print("  2. 机器人检测到剪贴板变化会自动AI回复")
        print("  3. 或者按 F1 键手动触发回复剪贴板内容")
        print("  4. 按 Ctrl+C 退出")
        print("=" * 50)

        # 监听剪贴板
        last_clipboard = pyperclip.paste()

        try:
            while self.running:
                # 检查剪贴板变化
                current_clipboard = pyperclip.paste()

                if current_clipboard != last_clipboard and current_clipboard:
                    last_clipboard = current_clipboard
                    content = current_clipboard.strip()

                    if len(content) > 1:
                        print(f"\n[检测到消息] {content[:50]}...")

                        # AI回复
                        print("AI思考中...")
                        reply = chat_with_ai(content, target_chat)

                        if reply:
                            print(f"[回复] {reply[:50]}...")
                            # 激活微信并发送
                            activate_wechat(self.hwnd)
                            time.sleep(0.3)
                            send_message(reply)

                time.sleep(1)

        except KeyboardInterrupt:
            self.running = False
            print("\n机器人已停止")


def main():
    print("=" * 50)
    print("微信AI自动回复机器人")
    print("=" * 50)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="测试发送")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--auto", action="store_true", help="自动回复模式(监听剪贴板)")
    parser.add_argument("--chat", default="文件传输助手", help="监听的聊天名称")
    args = parser.parse_args()

    bot = SimpleWechatBot()

    if args.test:
        bot.test_send()
    elif args.interactive:
        bot.run_interactive()
    elif args.auto:
        bot.auto_reply_mode(args.chat)
    else:
        print("\n用法:")
        print("  python simple_bot.py --test         测试发送")
        print("  python simple_bot.py --interactive  交互模式(手动输入)")
        print("  python simple_bot.py --auto         自动回复(监听剪贴板)")
        print("  python simple_bot.py --auto --chat 联系人名")


if __name__ == "__main__":
    main()