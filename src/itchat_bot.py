"""
微信机器人 - itchat-uos
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

import requests

try:
    import itchat_uos as itchat
except ImportError:
    import itchat

from itchat.content import TEXT


def chat_with_ai(message: str) -> str:
    """调用百炼API"""
    api_key = os.getenv("DASHSCOPE_API_KEY", "")
    model = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

    if not api_key:
        return "未配置API Key"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "input": {"messages": [{"role": "user", "content": message}]},
        "parameters": {"temperature": 0.8, "max_tokens": 100}
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


@itchat.msg_register(TEXT)
def reply_msg(msg):
    """处理文本消息"""
    # 打印收到的消息信息
    print(f"\n=== 新消息 ===")
    print(f"From: {msg.get('FromUserName', 'unknown')[:30]}")
    print(f"Text: {msg.get('Text', '')[:50]}")
    print(f"isSend: {msg.get('isSend', False)}")

    # 不回复自己发送的
    if msg.get('isSend', False):
        return

    # 不回复群消息
    from_user = msg.get('FromUserName', '')
    if '@chatroom' in from_user:
        return

    # 获取内容
    content = msg.get('Text', '')
    if not content:
        return

    # AI回复
    print("调用AI...")
    reply = chat_with_ai(content)

    if reply:
        print(f"回复: {reply[:50]}...")
        return reply
    return None


def main():
    print("=" * 50)
    print("微信机器人")
    print("=" * 50)

    print("\n扫码登录...")

    # 删除旧的登录缓存
    import glob
    for f in glob.glob(os.path.join(PROJECT_ROOT, "itchat.pkl*")):
        try:
            os.remove(f)
            print(f"清理缓存: {f}")
        except:
            pass

    # 登录
    itchat.auto_login(enableCmdQR=2)

    print("\n登录成功!")
    print("机器人运行中，按Ctrl+C退出\n")

    try:
        itchat.run()
    except KeyboardInterrupt:
        print("\n退出")


if __name__ == "__main__":
    main()