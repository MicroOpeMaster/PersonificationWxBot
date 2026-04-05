"""
微信机器人 - 基于 uiautomation 实现消息监听和自动回复
支持新版微信客户端，通过UI自动化操作
运行: python uia_bot.py
"""
import os
import sys
import time
import requests
import threading

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

try:
    import uiautomation as uia
except ImportError:
    print("请安装 uiautomation: pip install uiautomation")
    sys.exit(1)

import win32gui
import win32con


# ========== 配置 ===========
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")
AUTO_REPLY = True

# 对话历史
chat_history = {}
MAX_HISTORY = 10

# 已处理的消息ID
processed_msgs = set()


def find_wechat_window():
    """查找微信主窗口"""
    wechat_window = None

    def callback(hwnd, _):
        try:
            cls = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)
            # 微信主窗口
            if title == '微信' or title == 'WeChat':
                wechat_window = uia.WindowControl(handle=hwnd)
                return False
        except:
            pass
        return True

    win32gui.EnumWindows(callback, None)
    return wechat_window


def activate_wechat(hwnd):
    """激活微信窗口"""
    win32gui.ShowWindow(hwnd, win32con.SW_SHOW)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except:
        pass


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
            "result_format": "message"
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


class WechatUIBot:
    """基于UI自动化的微信机器人"""

    def __init__(self):
        self.wechat = None
        self.hwnd = None
        self.running = False
        self.last_messages = []
        self.current_chat = None

    def find_wechat(self):
        """查找并激活微信窗口"""
        print("查找微信窗口...")

        hwnd = None
        def callback(h, _):
            try:
                title = win32gui.GetWindowText(h)
                if title == '微信' or title == 'WeChat':
                    hwnd = h
                    return False
            except:
                pass
            return True

        win32gui.EnumWindows(callback, None)

        if not hwnd:
            print("未找到微信窗口！请确保微信PC客户端已打开并登录")
            return False

        self.hwnd = hwnd
        print(f"找到微信窗口: {hwnd}")

        # 激活窗口
        activate_wechat(hwnd)
        time.sleep(1)

        # 创建UI自动化控件
        self.wechat = uia.WindowControl(handle=hwnd)
        return True

    def get_current_chat_name(self):
        """获取当前聊天窗口的联系人名称"""
        try:
            # 获取聊天窗口标题区域的名称
            name_ctrl = self.wechat.TextControl(Name='聊天')
            if name_ctrl.Exists(0.5):
                # 尝试获取聊天对象名称
                parent = name_ctrl.GetParentControl()
                if parent:
                    for ctrl in parent.GetChildren():
                        if ctrl.ControlType == uia.ControlType.Text:
                            name = ctrl.Name
                            if name and name != '聊天':
                                return name
        except:
            pass

        # 另一种方式：从会话列表获取
        try:
            session_list = self.wechat.ListControl()
            if session_list.Exists(0.5):
                selected = session_list.GetSelectedItems()
                if selected:
                    return selected[0].Name
        except:
            pass

        return "未知"

    def get_messages(self):
        """获取当前聊天窗口的消息列表"""
        messages = []
        try:
            # 消息列表控件
            msg_list = self.wechat.ListControl()
            if msg_list.Exists(0.5):
                for item in msg_list.GetChildren():
                    try:
                        # 每个消息项可能包含多个文本控件
                        texts = []
                        for ctrl in item.GetChildren():
                            if ctrl.ControlType == uia.ControlType.Text:
                                texts.append(ctrl.Name)

                        if texts:
                            # 判断是否是收到的消息（不是自己发的）
                            # 通常自己发的消息在右侧，收到的在左侧
                            msg_text = ' '.join(texts)
                            # 获取消息发送者（第一个文本通常是发送者名或时间）
                            sender = texts[0] if texts[0] not in ['昨天', '今天', '前天'] else ''
                            content = texts[-1] if len(texts) > 1 else texts[0]

                            messages.append({
                                'sender': sender,
                                'content': content,
                                'is_send': False,  # 简化判断
                                'raw': texts
                            })
                    except:
                        continue
        except Exception as e:
            print(f"获取消息异常: {e}")

        return messages

    def send_message(self, message: str):
        """发送消息到当前聊天"""
        try:
            # 找到输入框
            input_ctrl = self.wechat.EditControl()
            if input_ctrl.Exists(0.5):
                # 激活输入框
                input_ctrl.Click()
                time.sleep(0.2)

                # 输入文本
                input_ctrl.SendKeys(message, waitTime=0.05)

                # 发送（按回车）
                time.sleep(0.2)
                input_ctrl.SendKeys('{Enter}')

                print(f"[发送成功] {message[:30]}...")
                return True
        except Exception as e:
            print(f"发送失败: {e}")

        return False

    def switch_to_chat(self, name: str):
        """切换到指定聊天"""
        try:
            # 使用搜索功能
            search_ctrl = self.wechat.EditControl(Name='搜索')
            if search_ctrl.Exists(0.5):
                search_ctrl.Click()
                time.sleep(0.3)

                # 清空并输入搜索内容
                search_ctrl.SendKeys('{Ctrl}a', waitTime=0.1)
                search_ctrl.SendKeys(name, waitTime=0.05)
                time.sleep(0.5)

                # 搜索结果中选择第一个
                search_ctrl.SendKeys('{Enter}')
                time.sleep(0.5)

                # 清空搜索框
                search_ctrl.SendKeys('{Esc}')
                return True
        except Exception as e:
            print(f"切换聊天失败: {e}")

        return False

    def monitor_loop(self):
        """消息监听循环"""
        print("\n开始监听消息...")

        while self.running:
            try:
                # 获取当前聊天名称
                current = self.get_current_chat_name()

                # 获取消息
                msgs = self.get_messages()

                if msgs:
                    for msg in msgs[-5:]:  # 只处理最近5条
                        content = msg['content']

                        # 创建消息标识
                        msg_id = f"{current}:{content}"

                        if msg_id not in processed_msgs:
                            processed_msgs.add(msg_id)

                            # 检查是否需要回复
                            if len(content.strip()) > 2 and content not in ['图片', '语音', '视频']:
                                print(f"\n[收到] {current}: {content[:50]}...")

                                # AI回复
                                print("AI思考中...")
                                reply = chat_with_ai(content, current)

                                if reply:
                                    print(f"[回复] {reply[:50]}...")
                                    # 确保窗口在前台
                                    activate_wechat(self.hwnd)
                                    time.sleep(0.3)
                                    self.send_message(reply)

                time.sleep(2)  # 轮询间隔

            except Exception as e:
                print(f"监听异常: {e}")
                time.sleep(5)

    def run(self):
        """运行机器人"""
        if not self.find_wechat():
            return

        self.running = True

        print("\n" + "=" * 50)
        print("机器人运行中...")
        print("=" * 50)
        print("当前会监听当前打开的聊天窗口")
        print("切换到要监听的聊天窗口，机器人会自动回复")
        print("按 Ctrl+C 退出")
        print("=" * 50)

        # 启动监听线程
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            print("\n机器人已停止")

    def test_send(self):
        """测试发送"""
        if not self.find_wechat():
            return

        print("\n测试发送消息...")
        print("请先打开一个聊天窗口")

        # 切换到文件传输助手
        self.switch_to_chat("文件传输助手")
        time.sleep(1)

        self.send_message("你好，这是机器人测试消息！")


def main():
    print("=" * 50)
    print("微信AI自动回复机器人 (UI自动化版)")
    print("=" * 50)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="测试发送")
    parser.add_argument("--run", action="store_true", help="运行机器人")
    args = parser.parse_args()

    bot = WechatUIBot()

    if args.test:
        bot.test_send()
    else:
        bot.run()


if __name__ == "__main__":
    main()