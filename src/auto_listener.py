"""
微信全自动监听模块
使用 wxauto 库实现消息监听和自动回复

注意：需要微信PC客户端 3.9.11.17 版本
下载地址：https://github.com/tom-snow/wechat-windows-versions/releases
"""
import time
import threading
import re
import sys
import win32gui
import win32con
from typing import Optional, Dict, List, Set

# 强制 stdout 行缓冲
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

try:
    import wxauto
except ImportError:
    wxauto = None

from src.config import (
    BOT_NAME, ALIAS_WHITELIST, ROOM_WHITELIST,
    AUTO_REPLY_PREFIX, LISTEN_INTERVAL, AUTO_REPLY_ENABLED
)
from src.model_api import BailianAPI, ChatHistoryManager


# 微信版本检测
def check_wechat_version() -> tuple:
    """
    检查微信窗口状态

    Returns:
        (hwnd, class_name, is_compatible)
    """
    # 先通过类名查找微信主窗口（wxauto 兼容版本）
    hwnd = win32gui.FindWindow('WeChatMainWndForPC', None)
    if hwnd != 0:
        return (hwnd, 'WeChatMainWndForPC', True)

    # 如果没找到，遍历所有窗口查找
    def find_wechat_main():
        result = (0, None, False)

        def enum_callback(hwnd, extra):
            class_name = win32gui.GetClassName(hwnd)
            title = win32gui.GetWindowText(hwnd)

            # 排除托盘窗口
            if class_name == 'TrayNotifyWnd':
                return True

            # 查找标题包含"微信"的窗口
            if '微信' in title:
                is_compatible = class_name == 'WeChatMainWndForPC'
                result = (hwnd, class_name, is_compatible)

            return True

        win32gui.EnumWindows(enum_callback, None)
        return result

    return find_wechat_main()


class AutoListener:
    """微信全自动监听回复"""

    # 微信窗口类名常量
    WX_COMPAT_CLASS = 'WeChatMainWndForPC'  # wxauto 兼容版本

    def __init__(self, api: BailianAPI, history_manager=None):
        self.api = api
        self.history = history_manager or ChatHistoryManager(max_history=10)
        self.wx: Optional[wxauto.WeChat] = None
        self.wx_hwnd: Optional[int] = None
        self.running = False
        self._thread: Optional[threading.Thread] = None

        # 监听的聊天列表
        self.listen_chats: Set[str] = set()

        # 已处理的消息ID，防止重复回复
        self._processed_msgs: Set[str] = set()

        # 是否使用 wxauto 模式
        self._use_wxauto = False

    def init(self) -> bool:
        """初始化微信连接"""
        # 先检查微信窗口状态
        hwnd, class_name, is_compatible = check_wechat_version()

        if hwnd == 0:
            print("错误: 未找到微信窗口")
            print("请确保微信PC客户端已启动并登录")
            return False

        print(f"检测到微信窗口 (类名: {class_name})")

        if not is_compatible:
            print("\n" + "=" * 50)
            print("当前微信版本不兼容 wxauto 库")
            print("=" * 50)
            print("需要安装微信 3.9.11.17 版本")
            print("下载地址: https://github.com/tom-snow/wechat-windows-versions/releases")
            print("")
            print("或使用热键模式: python main.py --mode hotkey")
            print("=" * 50)
            return False

        if wxauto is None:
            print("错误: wxauto 库未安装")
            print("请运行: pip install wxauto")
            return False

        try:
            self.wx = wxauto.WeChat()
            self.wx_hwnd = hwnd
            self._use_wxauto = True
            print("微信连接成功 (wxauto模式)")
            return True
        except Exception as e:
            print(f"微信连接失败: {e}")
            return False

    def setup_listen_chats(self) -> bool:
        """设置监听的聊天列表"""
        if not self.wx:
            return False

        # 添加私聊白名单
        for alias in ALIAS_WHITELIST:
            try:
                self.wx.AddListenChat(alias)
                self.listen_chats.add(alias)
                print(f"已添加监听: {alias}")
            except Exception as e:
                print(f"添加监听失败 {alias}: {e}")

        # 添加群聊白名单
        for room in ROOM_WHITELIST:
            try:
                self.wx.AddListenChat(room)
                self.listen_chats.add(room)
                print(f"已添加监听群: {room}")
            except Exception as e:
                print(f"添加监听群失败 {room}: {e}")

        if not self.listen_chats:
            print("警告: 未配置任何监听对象，请设置 ALIAS_WHITELIST 或 ROOM_WHITELIST")

        return len(self.listen_chats) > 0

    def should_reply(self, who: str, msg_type: int, sender: str, content: str) -> bool:
        """
        判断是否需要回复

        Args:
            who: 聊天对象名称（联系人名或群名）
            msg_type: 消息类型
            sender: 发送者名称
            content: 消息内容

        Returns:
            是否需要回复
        """
        content = content.strip()
        if not content:
            return False

        # 判断是否为群聊：通过 ROOM_WHITELIST 判断
        is_group = who in ROOM_WHITELIST

        if is_group:
            # 群聊：必须被@才回复
            if not BOT_NAME:
                return False

            # 检查是否被@
            if BOT_NAME not in content and "@" not in content:
                return False

            return True
        else:
            # 私聊：白名单检查
            if who not in ALIAS_WHITELIST:
                return False

        # 前缀匹配检查
        if AUTO_REPLY_PREFIX:
            if not content.startswith(AUTO_REPLY_PREFIX):
                return False

        return True

    def clean_content(self, content: str) -> str:
        """清理消息内容"""
        result = content.strip()
        if BOT_NAME:
            result = result.replace(BOT_NAME, '').strip()
        if AUTO_REPLY_PREFIX:
            result = result.replace(AUTO_REPLY_PREFIX, '').strip()
        # 移除可能的 @昵称 格式
        result = re.sub(r'@[^\s]+\s*', '', result).strip()
        return result

    def process_message(self, who: str, sender: str, content: str) -> Optional[str]:
        """
        处理单条消息，生成回复

        Args:
            who: 聊天对象
            sender: 发送者
            content: 消息内容

        Returns:
            AI回复内容
        """
        # 清理消息
        clean_msg = self.clean_content(content)
        if not clean_msg or len(clean_msg) < 1:
            return None

        print(f"\n[{who}] 收到消息: {clean_msg}")

        # 获取对话历史
        session_id = who
        history = self.history.get_history(session_id)

        # 调用 AI 生成回复
        print("正在生成AI回复...")
        reply = self.api.chat(clean_msg, history=history[:-1] if history else None)

        if reply:
            # 记录历史
            self.history.add_message(session_id, "user", clean_msg)
            self.history.add_message(session_id, "assistant", reply)
            print(f"AI回复: {reply}")
            return reply

        return None

    def send_reply(self, chat_window, reply: str) -> bool:
        """
        发送回复

        Args:
            chat_window: 聊天窗口对象或聊天名称
            reply: 回复内容

        Returns:
            是否成功
        """
        if not self.wx:
            return False

        try:
            # 如果传入的是 ChatWindow 对象，可以直接使用其 SendMsg 方法
            if hasattr(chat_window, 'SendMsg'):
                chat_window.SendMsg(reply)
                chat_name = getattr(chat_window, 'name', str(chat_window))
                print(f"已发送回复到 {chat_name}")
                return True
            else:
                # 使用 wx 对象的 SendMsg
                chat_name = str(chat_window)
                self.wx.SendMsg(reply, chat_name)
                print(f"已发送回复到 {chat_name}")
                return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False

    def _listen_loop(self):
        """监听循环（内部方法）"""
        print(f"开始监听... (间隔: {LISTEN_INTERVAL}秒)")

        while self.running:
            try:
                # 获取新消息
                msgs = self.wx.GetListenMessage()

                if msgs:
                    for chat_window, msg_list in msgs.items():
                        for msg in msg_list:
                            self._handle_message(chat_window, msg)

            except Exception as e:
                print(f"监听异常: {e}")

            time.sleep(LISTEN_INTERVAL)

    def _handle_message(self, chat_window, msg):
        """
        处理单条消息

        Args:
            chat_window: 聊天窗口对象（ChatWindow）
            msg: 消息内容（可能是列表、字符串或消息对象）
        """
        try:
            # 提取聊天名称
            # wxauto ChatWindow 的字符串格式: <wxauto Chat Window at 0x... for bot>
            # 从 "for xxx" 部分提取名称
            chat_window_str = str(chat_window)
            if ' for ' in chat_window_str:
                chat_name = chat_window_str.split(' for ')[-1].rstrip('>')
            else:
                chat_name = getattr(chat_window, 'name', chat_window_str)

            # 解析消息格式
            # wxauto 返回格式: [sender_type, content]
            # sender_type 可能是: 'SYS'(系统), 'Self'(自己), 'friend'(好友), 或具体昵称
            if isinstance(msg, (list, tuple)) and len(msg) >= 2:
                sender_type = msg[0]
                content = msg[1]
                sender = sender_type
            elif isinstance(msg, str):
                content = msg
                sender = 'friend'
            elif isinstance(msg, dict):
                content = msg.get('content', '')
                sender = msg.get('sender', chat_name)
            else:
                content = getattr(msg, 'content', str(msg))
                sender = getattr(msg, 'sender', chat_name)

            # 过滤系统消息和自己发的消息
            if sender == 'SYS' or sender == 'Self':
                return

            # 生成唯一消息ID防止重复处理
            msg_id = f"{chat_name}:{sender}:{content[:50]}"
            if msg_id in self._processed_msgs:
                return
            self._processed_msgs.add(msg_id)

            # 判断是否需要回复
            if self.should_reply(chat_name, None, sender, content):
                reply = self.process_message(chat_name, sender, content)
                if reply:
                    self.send_reply(chat_window, reply)

        except Exception as e:
            print(f"处理消息异常: {e}")

    def start(self):
        """启动监听"""
        if not self.init():
            print("初始化失败")
            return False

        if not self.setup_listen_chats():
            print("未设置监听对象")
            return False

        self.running = True
        self._thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._thread.start()

        print("\n" + "=" * 50)
        print("微信全自动监听已启动")
        print("=" * 50)
        print(f"监听对象: {', '.join(self.listen_chats) or '无'}")
        print(f"机器人名称: {BOT_NAME or '未设置'}")
        print(f"监听间隔: {LISTEN_INTERVAL}秒")
        print("")
        print("按 Ctrl+C 停止")
        print("=" * 50)

        return True

    def stop(self):
        """停止监听"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)
        print("\n监听已停止")

    def run(self):
        """运行监听（阻塞式）"""
        if self.start():
            try:
                # 保持主线程运行
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                self.stop()


def create_listener(api_key=None, model=None) -> AutoListener:
    """创建监听器"""
    from src.config import DASHSCOPE_API_KEY, DASHSCOPE_FINETUNED_MODEL, DASHSCOPE_MODEL
    api_key = api_key or DASHSCOPE_API_KEY
    model = model or DASHSCOPE_FINETUNED_MODEL or DASHSCOPE_MODEL
    api = BailianAPI(api_key=api_key, model=model)
    return AutoListener(api=api)


if __name__ == "__main__":
    # 测试监听
    listener = create_listener()
    listener.run()