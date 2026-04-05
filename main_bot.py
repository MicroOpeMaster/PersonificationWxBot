"""
微信机器人 - 完整版
支持扫码登录、消息监听、AI自动回复
运行: python main_bot.py
"""
import os
import sys
import time
import requests

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

# 使用 itchat-uos (支持更多账号)
try:
    import itchat_uos as itchat
except ImportError:
    import itchat

from itchat.content import TEXT, PICTURE, VIDEO, MAP, CARD, SHARING


# ========== 配置 ==========
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")
AUTO_REPLY = os.getenv("WECHAT_AUTO_REPLY", "true").lower() == "true"

# 不回复的关键词
FILTER_WORDS = ["转账", "红包", "收款", "付款", "位置分享", "语音通话", "视频通话"]

# 对话历史 (简单内存存储)
chat_history = {}
MAX_HISTORY = 10


def chat_with_ai(message: str, sender: str = "") -> str:
    """调用阿里云百炼API获取回复"""
    if not API_KEY:
        return "API Key未配置"

    # 获取对话历史
    history = chat_history.get(sender, [])

    # 构建消息列表
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
            headers=headers,
            json=payload,
            timeout=30
        )

        if resp.status_code == 200:
            result = resp.json()
            reply = result.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")

            # 更新历史
            if sender:
                if sender not in chat_history:
                    chat_history[sender] = []
                chat_history[sender].append({"role": "user", "content": message})
                chat_history[sender].append({"role": "assistant", "content": reply})
                # 保持历史长度
                if len(chat_history[sender]) > MAX_HISTORY * 2:
                    chat_history[sender] = chat_history[sender][-MAX_HISTORY * 2:]

            return reply

    except Exception as e:
        print(f"[API异常] {e}")

    return None


def should_reply(msg) -> bool:
    """判断是否应该回复"""
    if not AUTO_REPLY:
        return False

    # 不回复自己发送的消息
    if msg.get('isSend', False):
        return False

    # 不回复群消息
    from_user = msg.get('FromUserName', '')
    if '@chatroom' in from_user:
        return False

    # 获取内容
    content = msg.get('Text', '')

    # 过滤关键词
    for word in FILTER_WORDS:
        if word in content:
            return False

    # 过滤太短的消息
    if len(content.strip()) < 2:
        return False

    return True


@itchat.msg_register(TEXT)
def handle_text(msg):
    """处理文本消息"""
    sender = msg.get('FromUserName', '')
    sender_name = itchat.search_friends(userName=sender).get('NickName', sender) if sender else 'Unknown'
    content = msg.get('Text', '')

    print(f"\n[收到消息] {sender_name}: {content[:80]}...")

    if not should_reply(msg):
        print("[跳过] 不满足回复条件")
        return None

    # AI回复
    print("AI思考中...")
    reply = chat_with_ai(content, sender)

    if reply:
        print(f"[回复] {reply[:80]}...")
        return reply

    return None


@itchat.msg_register([PICTURE, VIDEO, MAP, CARD, SHARING])
def handle_other(msg):
    """处理其他类型消息(只打印不回复)"""
    sender = msg.get('FromUserName', '')
    sender_name = itchat.search_friends(userName=sender).get('NickName', sender) if sender else 'Unknown'
    msg_type = msg.get('Type', 'Unknown')

    print(f"\n[收到{msg_type}] {sender_name}")
    return None


def main():
    print("=" * 60)
    print("         微信AI自动回复机器人")
    print("=" * 60)
    print(f"API: {MODEL}")
    print(f"自动回复: {AUTO_REPLY}")
    print("=" * 60)

    # 清理旧的登录缓存
    import glob
    cache_files = glob.glob(os.path.join(PROJECT_ROOT, "itchat.pkl*"))
    for f in cache_files:
        try:
            os.remove(f)
            print(f"清理缓存: {f}")
        except:
            pass

    print("\n请用手机微信扫码登录...")
    print("如果二维码显示不正常，请直接在终端查看\n")

    # 登录 (enableCmdQR=2 在Windows终端显示二维码)
    itchat.auto_login(
        enableCmdQR=2,
        hotReload=False,  # 每次重新登录
        statusStorageDir=os.path.join(PROJECT_ROOT, 'itchat_status.pkl')
    )

    print("\n✓ 登录成功!")
    print("机器人已启动，开始监听消息...")
    print("按 Ctrl+C 停止运行\n")

    # 运行
    try:
        itchat.run()
    except KeyboardInterrupt:
        print("\n机器人已停止")


if __name__ == "__main__":
    main()