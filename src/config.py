"""
配置模块
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 阿里云百炼配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen-turbo")
DASHSCOPE_FINETUNED_MODEL = os.getenv("DASHSCOPE_FINETUNED_MODEL", "")

# 系统提示词
SYSTEM_PROMPT = os.getenv("SYSTEM_PROMPT", "")

# 微信机器人配置
BOT_NAME = os.getenv("BOT_NAME", "")  # 机器人名称，群聊@识别
ALIAS_WHITELIST = [x.strip() for x in os.getenv("ALIAS_WHITELIST", "").split(",") if x.strip()]
ROOM_WHITELIST = [x.strip() for x in os.getenv("ROOM_WHITELIST", "").split(",") if x.strip()]
AUTO_REPLY_PREFIX = os.getenv("AUTO_REPLY_PREFIX", "")

# 数据处理配置
DATA_SOURCE_DIR = os.getenv("DATA_SOURCE_DIR", "./data/raw")
DATA_OUTPUT_DIR = os.getenv("DATA_OUTPUT_DIR", "./data/processed")
MIN_TRAIN_SAMPLES = int(os.getenv("MIN_TRAIN_SAMPLES", "500"))

# 自动监听配置
LISTEN_INTERVAL = float(os.getenv("LISTEN_INTERVAL", "1.0"))  # 监听间隔（秒）
AUTO_REPLY_ENABLED = os.getenv("AUTO_REPLY_ENABLED", "true").lower() == "true"  # 是否启用自动回复