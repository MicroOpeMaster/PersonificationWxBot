"""
微信机器人模块
实现消息监听和自动回复
"""
import time
import random
from typing import Optional
from src.config import WECHAT_AUTO_REPLY, WECHAT_REPLY_PREFIX, WECHAT_REPLY_SUFFIX
from src.model_api import BailianAPI, ChatHistoryManager


class WeChatBot:
    """微信自动回复机器人"""

    def __init__(self, api: BailianAPI, auto_reply: bool = True):
        self.api = api
        self.auto_reply = auto_reply
        self.history_manager = ChatHistoryManager(max_history=10)

        # 回复延迟设置 (模拟真人回复)
        self.min_delay = 1
        self.max_delay = 5

        # 过滤关键词 (不回复的消息)
        self.filter_keywords = [
            "转账", "红包", "收款", "付款",
            "位置分享", "语音通话", "视频通话"
        ]

        # 白名单联系人 (可选)
        self.whitelist: list = []

        # 黑名单联系人 (可选)
        self.blacklist: list = []

    def should_reply(self, message: str, sender: str) -> bool:
        """判断是否应该回复"""
        if not self.auto_reply:
            return False

        # 黑名单检查
        if sender in self.blacklist:
            return False

        # 白名单检查 (如果有白名单则只回复白名单)
        if self.whitelist and sender not in self.whitelist:
            return False

        # 过滤关键词检查
        for keyword in self.filter_keywords:
            if keyword in message:
                return False

        # 过滤太短的消息
        if len(message.strip()) < 2:
            return False

        return True

    def get_reply(self, message: str, sender: str) -> Optional[str]:
        """获取AI回复"""
        session_id = sender

        # 添加用户消息到历史
        self.history_manager.add_message(session_id, "user", message)

        # 获取历史上下文
        history = self.history_manager.get_history(session_id)

        # 调用API获取回复
        reply = self.api.chat(message, history=history[:-1])

        if reply:
            # 添加回复到历史
            self.history_manager.add_message(session_id, "assistant", reply)

            # 添加前缀后缀
            if WECHAT_REPLY_PREFIX:
                reply = WECHAT_REPLY_PREFIX + reply
            if WECHAT_REPLY_SUFFIX:
                reply = reply + WECHAT_REPLY_SUFFIX

        return reply

    def simulate_human_delay(self):
        """模拟真人回复延迟"""
        delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(delay)

    def handle_message(self, msg_type: str, content: str, sender: str, sender_name: str = ""):
        """
        处理收到的消息

        Args:
            msg_type: 消息类型
            content: 消息内容
            sender: 发送者微信ID
            sender_name: 发送者昵称
        """
        print(f"[收到消息] {sender_name or sender}: {content[:50]}...")

        # 只处理文本消息
        if msg_type != "文本消息":
            return

        # 判断是否回复
        if not self.should_reply(content, sender):
            print(f"[跳过] 不满足回复条件")
            return

        # 模拟延迟
        # self.simulate_human_delay()

        # 获取回复
        reply = self.get_reply(content, sender)

        if reply:
            print(f"[回复] {reply[:50]}...")
            return reply
        else:
            print("[失败] API未返回回复")
            return None


class WeChatNTWorkBot(WeChatBot):
    """基于ntwork库的微信机器人"""

    def __init__(self, api: BailianAPI):
        super().__init__(api)
        self.wx = None

    def init_wechat(self):
        """初始化微信连接"""
        try:
            import ntwork
            self.wx = ntwork.WeChat()
            self.wx.wait_login()
            print("微信登录成功!")
            return True
        except ImportError:
            print("请安装ntwork库: pip install ntwork")
            return False
        except Exception as e:
            print(f"微信初始化失败: {e}")
            return False

    def on_message_callback(self, msg):
        """消息回调处理"""
        msg_type = msg.get("type", "")
        content = msg.get("content", "")
        sender = msg.get("sender_username", "")
        sender_name = msg.get("sender_display_name", "")

        reply = self.handle_message(msg_type, content, sender, sender_name)

        if reply:
            # 发送回复
            self.wx.send_text(sender, reply)

    def run(self):
        """运行机器人"""
        if not self.init_wechat():
            return

        # 注册消息回调
        self.wx.on_message = self.on_message_callback

        print("机器人开始运行...")
        print("按 Ctrl+C 停止")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("机器人已停止")


class MockWeChatBot(WeChatBot):
    """模拟机器人 (用于测试)"""

    def run_interactive(self):
        """交互式测试模式"""
        print("=" * 50)
        print("微信机器人测试模式")
        print("=" * 50)
        print("输入消息进行测试，输入 'quit' 退出")

        sender = "test_user"
        sender_name = "测试用户"

        while True:
            try:
                message = input("\n请输入消息: ").strip()

                if message.lower() == 'quit':
                    print("退出测试模式")
                    break

                if not message:
                    continue

                reply = self.handle_message("文本消息", message, sender, sender_name)

                if reply:
                    print(f"\n机器人回复: {reply}")

            except KeyboardInterrupt:
                print("\n退出测试模式")
                break


def main():
    """主函数"""
    # 创建API实例
    api = BailianAPI()

    # 选择运行模式
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mock", action="store_true", help="使用模拟测试模式")
    parser.add_argument("--real", action="store_true", help="连接真实微信")
    args = parser.parse_args()

    if args.mock:
        # 测试模式
        bot = MockWeChatBot(api)
        bot.run_interactive()
    elif args.real:
        # 真实微信模式
        bot = WeChatNTWorkBot(api)
        bot.run()
    else:
        print("请指定运行模式:")
        print("  --mock: 模拟测试模式")
        print("  --real: 连接真实微信")


if __name__ == "__main__":
    main()