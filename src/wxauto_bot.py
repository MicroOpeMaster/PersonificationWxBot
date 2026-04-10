"""
微信机器人模块 - 使用热键触发
用户在微信中查看消息后按热键触发自动回复
"""
import time
import threading
import pyperclip
import pyautogui
import win32gui
import win32con
import keyboard
from typing import Optional, Callable

from src.config import BOT_NAME, ALIAS_WHITELIST, ROOM_WHITELIST, AUTO_REPLY_PREFIX
from src.model_api import BailianAPI, ChatHistoryManager

pyautogui.PAUSE = 0.15
pyautogui.FAILSAFE = True


class WeChatController:
    """微信窗口控制"""

    def __init__(self):
        self.handle = None
        self.rect = None

    def find_window(self) -> bool:
        self.handle = win32gui.FindWindow(None, "微信")
        if self.handle == 0:
            print("未找到微信窗口")
            return False
        self.rect = win32gui.GetWindowRect(self.handle)
        print("微信窗口已连接")
        return True

    def activate(self) -> bool:
        if self.handle:
            try:
                win32gui.ShowWindow(self.handle, win32con.SW_RESTORE)
                time.sleep(0.2)
                win32gui.SetForegroundWindow(self.handle)
                time.sleep(0.3)
                return True
            except:
                return False
        return False

    def open_chat(self, name: str) -> bool:
        try:
            self.activate()
            time.sleep(0.3)

            pyautogui.hotkey('ctrl', 'f')
            time.sleep(0.5)

            pyperclip.copy(name)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.5)

            pyautogui.press('enter')
            time.sleep(0.3)

            pyautogui.press('esc')
            time.sleep(0.2)

            return True
        except Exception as e:
            print(f"打开聊天失败: {e}")
            return False

    def send_message(self, message: str) -> bool:
        try:
            self.activate()
            time.sleep(0.2)

            left, top, right, bottom = self.rect
            width = right - left
            height = bottom - top

            input_x = left + width // 2
            input_y = bottom - 60

            pyautogui.click(input_x, input_y)
            time.sleep(0.2)

            pyperclip.copy(message)
            pyautogui.hotkey('ctrl', 'v')
            time.sleep(0.3)
            pyautogui.press('enter')

            return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False


class WxAutoBot:
    """微信机器人 - 热键触发模式"""

    def __init__(self, api: BailianAPI, history_manager=None):
        self.api = api
        self.history = history_manager or ChatHistoryManager(max_history=10)
        self.wx = WeChatController()
        self.running = False

        # 当前联系人
        self.current_contact = None

    def init(self) -> bool:
        return self.wx.find_window()

    def clean_content(self, content: str) -> str:
        result = content
        if BOT_NAME:
            result = result.replace(BOT_NAME, '').strip()
        if AUTO_REPLY_PREFIX:
            result = result.replace(AUTO_REPLY_PREFIX, '').strip()
        return result.strip()

    def reply_to_message(self, message: str, contact: str = None) -> Optional[str]:
        """
        根据消息内容生成并发送回复

        Args:
            message: 收到的消息内容
            contact: 联系人名称（可选，用于历史记录）

        Returns:
            AI回复内容
        """
        try:
            contact = contact or self.current_contact or "default"

            # 清理消息
            clean_msg = self.clean_content(message)
            if not clean_msg or len(clean_msg) < 1:
                print("消息内容无效")
                return None

            print(f"\n收到消息: {clean_msg}")
            print("正在生成AI回复...")

            # 获取AI回复
            history = self.history.get_history(contact)
            reply = self.api.chat(clean_msg, history=history[:-1] if history else None)

            if reply:
                # 记录历史
                self.history.add_message(contact, "user", clean_msg)
                self.history.add_message(contact, "assistant", reply)

                # 发送回复
                self.wx.send_message(reply)
                print(f"已回复: {reply}")

                return reply

            return None

        except Exception as e:
            print(f"回复失败: {e}")
            return None

    def on_hotkey(self):
        """热键回调：从剪贴板获取消息并回复"""
        print("\n[热键触发] 获取剪贴板内容...")
        message = pyperclip.paste()

        if not message:
            print("剪贴板为空，请先复制消息内容")
            return

        self.reply_to_message(message)

    def on_hotkey_with_contact(self):
        """热键回调：设置当前联系人"""
        contact = pyperclip.paste()
        if contact:
            self.current_contact = contact.strip()
            print(f"\n已设置当前联系人: {self.current_contact}")
        else:
            print("剪贴板为空")

    def start(self):
        """启动"""
        if not self.init():
            return False

        self.running = True

        # 注册热键
        # F1: 使用剪贴板内容作为消息并回复
        # F2: 设置当前联系人（从剪贴板）
        # F3: 打开当前联系人的聊天窗口
        keyboard.add_hotkey('f1', self.on_hotkey)
        keyboard.add_hotkey('f2', self.on_hotkey_with_contact)
        keyboard.add_hotkey('f3', self.open_current_chat)

        print("\n" + "=" * 50)
        print("微信机器人已启动 (热键模式)")
        print("=" * 50)
        print("热键说明:")
        print("  F1 - 回复剪贴板中的消息内容")
        print("  F2 - 设置当前联系人（从剪贴板）")
        print("  F3 - 打开当前联系人的聊天窗口")
        print("")
        print("使用方法:")
        print("  1. 在微信中复制收到的消息")
        print("  2. 按 F1 生成并发送AI回复")
        print("")
        print(f"当前联系人: {self.current_contact or '未设置'}")
        print("按 ESC 退出")
        print("=" * 50)

        # 等待 ESC 退出
        keyboard.wait('esc')
        self.stop()

        return True

    def open_current_chat(self):
        """打开当前联系人的聊天窗口"""
        if self.current_contact:
            self.wx.open_chat(self.current_contact)
            print(f"已打开: {self.current_contact}")
        else:
            print("请先设置联系人 (F2)")

    def stop(self):
        self.running = False
        keyboard.unhook_all()
        print("\n机器人已停止")

    def run(self):
        self.start()


def create_bot(api_key=None, model=None) -> WxAutoBot:
    from src.config import DASHSCOPE_API_KEY, DASHSCOPE_FINETUNED_MODEL, DASHSCOPE_MODEL
    api_key = api_key or DASHSCOPE_API_KEY
    model = model or DASHSCOPE_FINETUNED_MODEL or DASHSCOPE_MODEL
    api = BailianAPI(api_key=api_key, model=model)
    return WxAutoBot(api=api)