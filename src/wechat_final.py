"""
微信机器人 - 最终稳定版

运行方式:
    python src/wechat_final.py

说明:
    这是一个简化的微信机器人，使用itchat-uos
    如果登录失败，说明该账号不支持Web微信
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# 清理可能的缓存文件
for cache_file in ['itchat.pkl', 'itchat.pkl1']:
    cache_path = os.path.join(PROJECT_ROOT, cache_file)
    if os.path.exists(cache_path):
        try:
            os.remove(cache_path)
        except:
            pass

from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, '.env'))

import requests

print("正在加载itchat...")
try:
    import itchat_uos as itchat
    print("使用 itchat-uos")
except ImportError:
    import itchat
    print("使用 itchat")

from itchat.content import TEXT, PICTURE, RECORDING

# API配置
API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")

# 过滤名单
EXCLUDE_USERS = ['filehelper', 'weixin', 'newsapp']


def call_api(message: str) -> str:
    """调用百炼API"""
    if not API_KEY:
        return None

    try:
        resp = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "input": {"messages": [{"role": "user", "content": message}]},
                "parameters": {"temperature": 0.8, "max_tokens": 100}
            },
            timeout=30
        )

        if resp.status_code == 200:
            data = resp.json()
            choices = data.get("output", {}).get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
    except Exception as e:
        print(f"[API错误] {e}")

    return None


# 消息计数
msg_count = 0


@itchat.msg_register(TEXT)
def on_text(msg):
    """文本消息处理"""
    global msg_count
    msg_count += 1

    from_user = msg.get('FromUserName', '')
    to_user = msg.get('ToUserName', '')
    content = msg.get('Text', '')
    is_send = msg.get('isSend', False)

    # 日志
    print(f"\n[消息#{msg_count}] {'发送' if is_send else '接收'}")
    print(f"  From: {from_user[:25]}...")
    print(f"  Text: {content[:40]}")

    # 自己发送的不回复
    if is_send:
        return

    # 群消息不回复
    if '@chatroom' in from_user:
        print("  -> 群消息，忽略")
        return

    # 过滤特殊用户
    for ex in EXCLUDE_USERS:
        if ex in from_user.lower():
            print("  -> 系统消息，忽略")
            return

    # 调用AI
    print("  -> 调用AI...")
    reply = call_api(content)

    if reply:
        print(f"  -> 回复: {reply[:40]}...")
        try:
            itchat.send(reply, toUserName=from_user)
            print("  -> 发送成功")
        except Exception as e:
            print(f"  -> 发送失败: {e}")
    else:
        print("  -> AI无响应")


@itchat.msg_register(PICTURE)
def on_picture(msg):
    print(f"\n[图片消息]")


@itchat.msg_register(RECORDING)
def on_voice(msg):
    print(f"\n[语音消息]")


def main():
    print("=" * 50)
    print("微信机器人 - 最终版")
    print("=" * 50)
    print(f"API Key: {'已配置' if API_KEY else '未配置'}")
    print(f"Model: {MODEL}")

    print("\n正在登录...")
    print("请用手机微信扫描二维码\n")

    try:
        # 不使用hotReload，全新登录
        itchat.auto_login(enableCmdQR=2, statusStorageDir='itchat.pkl')
    except Exception as e:
        print(f"\n登录失败: {e}")
        print("\n可能原因:")
        print("1. 账号不支持Web微信(2017年后注册)")
        print("2. 网络问题")
        return

    print("\n" + "=" * 50)
    print("登录成功! 机器人已启动")
    print("=" * 50)
    print("向我发送消息测试...")
    print("按 Ctrl+C 退出\n")

    try:
        itchat.run()
    except KeyboardInterrupt:
        print("\n\n已退出")
        itchat.logout()


if __name__ == "__main__":
    main()