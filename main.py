"""
微信AI聊天机器人主入口
"""
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

from src.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL, DASHSCOPE_FINETUNED_MODEL
from src.wxauto_bot import WxAutoBot
from src.auto_listener import AutoListener
from src.model_api import BailianAPI, ChatHistoryManager


def main():
    parser = argparse.ArgumentParser(description='微信AI聊天机器人')
    parser.add_argument('--mode', choices=['auto', 'hotkey'], default='auto',
                        help='运行模式: auto=全自动监听, hotkey=热键触发')
    args = parser.parse_args()

    print("=" * 50, flush=True)
    print("微信AI聊天机器人", flush=True)
    print("=" * 50, flush=True)

    if not DASHSCOPE_API_KEY:
        print("错误: 请配置 DASHSCOPE_API_KEY", flush=True)
        return

    model = DASHSCOPE_FINETUNED_MODEL or DASHSCOPE_MODEL
    print(f"模型: {model}", flush=True)
    print(f"模式: {args.mode}", flush=True)

    # 创建 API 实例
    api = BailianAPI(api_key=DASHSCOPE_API_KEY, model=model)

    if args.mode == 'auto':
        # 全自动监听模式
        listener = AutoListener(api=api)
        listener.run()
    else:
        # 热键触发模式
        bot = WxAutoBot(api=api)
        bot.run()


if __name__ == "__main__":
    main()