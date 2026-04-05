"""
微信自动监听回复机器人 - wxauto版本
需要微信PC客户端版本 3.9.11.17
默认监听所有私聊消息

运行: python wxauto_bot.py --run
"""
import os
import sys
import time
import requests

# 设置标准输出编码
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 项目根目录
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

from wxauto import WeChat


# ========== 配置 ==========
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

# 调试：打印配置
if not API_KEY:
    print(f"[警告] 未加载到API Key，.env路径: {os.path.join(PROJECT_ROOT, '.env')}")

# 不回复的关键词
FILTER_WORDS = ["转账", "红包", "收款", "付款", "位置", "语音", "视频"]

# 是否回复群消息
REPLY_GROUP = False

# 对话历史
chat_history = {}
MAX_HISTORY = 10

# 已处理的消息ID
processed_msg_ids = set()


def chat_with_ai(message: str, sender: str) -> str:
    """调用阿里云百炼API获取回复"""
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


def should_reply(content: str, chat: str) -> bool:
    """判断是否应该回复"""
    if len(content.strip()) < 2:
        return False

    for word in FILTER_WORDS:
        if word in content:
            return False

    # 群消息过滤
    if not REPLY_GROUP:
        if '群' in chat or '@chatroom' in chat.lower():
            return False

    return True


class WxAutoBot:
    """wxauto微信机器人"""

    def __init__(self):
        self.wx = None
        self.running = False

    def init(self):
        """初始化"""
        print("连接微信...")
        try:
            self.wx = WeChat()
            print(f"登录用户: {self.wx.nickname}")
            return True
        except Exception as e:
            print(f"连接失败: {e}")
            print("请确保微信版本为 3.9.11.17")
            return False

    def get_all_messages(self):
        """获取当前聊天窗口所有消息"""
        try:
            msgs = self.wx.GetAllMessage()
            return msgs
        except Exception as e:
            return []

    def send_msg(self, msg: str):
        """发送消息到当前聊天"""
        try:
            self.wx.SendMsg(msg)
            return True
        except Exception as e:
            print(f"发送失败: {e}")
            return False

    def switch_chat(self, name: str):
        """切换到指定聊天"""
        try:
            self.wx.ChatWith(name)
            time.sleep(0.5)
            return True
        except:
            return False

    def get_current_chat(self):
        """获取当前聊天名称"""
        try:
            # 从会话列表获取当前选中的
            sessions = self.wx.GetSessionList()
            # wxauto 当前聊天可以通过 CurrentChat 获取
            current = self.wx.CurrentChat()
            return current
        except:
            return None

    def run_polling(self):
        """轮询模式 - 遍历所有会话检查新消息"""
        if not self.init():
            return

        print("\n获取会话列表...")
        sessions = self.wx.GetSessionList()

        if isinstance(sessions, dict):
            # 过滤群聊和系统消息
            chat_list = []
            for name in sessions.keys():
                # 跳过系统消息
                if name in ['微信团队', '微信支付', '服务通知']:
                    continue
                # 跳过群聊（如果不回复群）
                if not REPLY_GROUP and ('群' in name or name.endswith('群')):
                    continue
                chat_list.append(name)
        else:
            chat_list = list(sessions)

        print(f"监听 {len(chat_list)} 个私聊会话")

        self.running = True

        print("\n" + "=" * 50)
        print("机器人运行中 (轮询模式)")
        print("=" * 50)
        print("自动遍历所有私聊，检查新消息并回复")
        print("按 Ctrl+C 退出")
        print("=" * 50 + "\n")

        # 记录每个聊天的最后消息ID
        last_msg_map = {}

        try:
            while self.running:
                for chat_name in chat_list:
                    try:
                        # 切换到该聊天
                        self.wx.ChatWith(chat_name)
                        time.sleep(0.3)

                        # 获取消息
                        msgs = self.wx.GetAllMessage()

                        if not msgs:
                            continue

                        # 获取最后一条消息
                        for msg in msgs[-3:]:
                            msg_type = msg.type if hasattr(msg, 'type') else ''
                            sender = msg.sender if hasattr(msg, 'sender') else ''
                            content = msg.content if hasattr(msg, 'content') else str(msg)
                            msg_id = msg.id if hasattr(msg, 'id') else ''

                            # 跳过系统消息、时间消息、撤回消息
                            if msg_type in ('sys', 'time', 'recall'):
                                continue

                            # 跳过自己发的消息
                            if msg_type == 'self' or sender == 'Self':
                                continue

                            # 消息去重
                            if msg_id and msg_id in processed_msg_ids:
                                continue

                            if msg_id:
                                processed_msg_ids.add(msg_id)

                            # 检查是否需要回复
                            if not should_reply(content, chat_name):
                                continue

                            # 回复消息
                            print(f"\n[{chat_name}] {sender}: {content[:50]}...")
                            print("AI思考中...")

                            reply = chat_with_ai(content, chat_name)

                            if reply:
                                print(f"[回复] {reply[:50]}...")
                                self.send_msg(reply)
                                time.sleep(0.5)

                        # 记录最后消息
                        if msgs:
                            last_msg = msgs[-1]
                            if hasattr(last_msg, 'id'):
                                last_msg_map[chat_name] = last_msg.id

                    except Exception as e:
                        # 某个聊天出错，继续下一个
                        pass

                # 清理已处理消息记录
                if len(processed_msg_ids) > 500:
                    processed_msg_ids.clear()

                # 等待下一次轮询
                time.sleep(3)

        except KeyboardInterrupt:
            self.running = False
            print("\n机器人已停止")

    def run_listen(self):
        """监听模式 - 使用wxauto的AddListenChat"""
        if not self.init():
            return

        print("\n获取会话列表...")
        sessions = self.wx.GetSessionList()

        if isinstance(sessions, dict):
            chat_list = []
            for name in sessions.keys():
                if name in ['微信团队', '微信支付', '服务通知']:
                    continue
                if not REPLY_GROUP and ('群' in name):
                    continue
                chat_list.append(name)
        else:
            chat_list = list(sessions)

        # 只监听前5个，避免性能问题
        monitor_list = chat_list[:5]
        print(f"监听 {len(monitor_list)} 个会话 (最多5个)")

        for name in monitor_list:
            try:
                self.wx.AddListenChat(who=name)
                print(f"  + {name}")
            except Exception as e:
                print(f"  失败: {name}")

        self.running = True

        print("\n" + "=" * 50)
        print("机器人运行中 (监听模式)")
        print("=" * 50)
        print("按 Ctrl+C 退出")
        print("=" * 50 + "\n")

        try:
            while self.running:
                msgs = self.wx.GetListenMessage()

                for chat, msg_list in msgs.items():
                    for msg in msg_list:
                        msg_type = msg.type if hasattr(msg, 'type') else ''
                        sender = msg.sender if hasattr(msg, 'sender') else ''
                        content = msg.content if hasattr(msg, 'content') else str(msg)
                        msg_id = msg.id if hasattr(msg, 'id') else ''

                        if msg_type in ('sys', 'time', 'recall'):
                            continue

                        if msg_type == 'self' or sender == 'Self':
                            continue

                        if msg_id and msg_id in processed_msg_ids:
                            continue

                        if msg_id:
                            processed_msg_ids.add(msg_id)

                        if not should_reply(content, chat):
                            continue

                        print(f"\n[{chat}] {sender}: {content[:50]}...")
                        print("AI思考中...")

                        reply = chat_with_ai(content, chat)

                        if reply:
                            print(f"[回复] {reply[:50]}...")
                            self.wx.SendMsg(reply, chat)

                time.sleep(1)

        except KeyboardInterrupt:
            self.running = False
            print("\n机器人已停止")

    def interactive(self):
        """交互模式"""
        if not self.init():
            return

        print("\n" + "=" * 50)
        print("交互模式")
        print("=" * 50)
        print("输入: 联系人:消息")
        print("例如: 陈胜富:你好")
        print("quit 退出")
        print("=" * 50 + "\n")

        while True:
            try:
                inp = input("> ").strip()
                if inp.lower() == 'quit':
                    break

                if ':' not in inp:
                    print("格式: 联系人:消息")
                    continue

                who, msg = inp.split(':', 1)
                who, msg = who.strip(), msg.strip()

                if who and msg:
                    print("AI思考中...")
                    reply = chat_with_ai(msg, who)

                    if reply:
                        print(f"AI: {reply[:80]}...")
                        self.wx.ChatWith(who)
                        time.sleep(0.3)
                        self.send_msg(reply)

            except KeyboardInterrupt:
                break

        print("\n已退出")

    def test(self):
        """测试"""
        if not self.init():
            return

        print("\n测试发送到文件传输助手...")
        self.wx.ChatWith("文件传输助手")
        time.sleep(0.5)
        self.send_msg("机器人测试消息!")
        print("已发送")


def main():
    print("=" * 50)
    print("微信自动监听回复机器人")
    print("=" * 50)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", action="store_true", help="运行轮询模式")
    parser.add_argument("--listen", action="store_true", help="运行监听模式(最多5个)")
    parser.add_argument("--interactive", action="store_true", help="交互模式")
    parser.add_argument("--test", action="store_true", help="测试")
    args = parser.parse_args()

    bot = WxAutoBot()

    if args.test:
        bot.test()
    elif args.interactive:
        bot.interactive()
    elif args.listen:
        bot.run_listen()
    elif args.run:
        bot.run_polling()
    else:
        print("\n用法:")
        print("  python wxauto_bot.py --run         轮询模式(监听所有私聊)")
        print("  python wxauto_bot.py --listen      监听模式(最多5个)")
        print("  python wxauto_bot.py --interactive 交互模式")
        print("  python wxauto_bot.py --test        测试")


if __name__ == "__main__":
    main()