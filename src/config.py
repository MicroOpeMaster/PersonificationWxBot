"""
配置模块
"""
import os
from dotenv import load_dotenv

load_dotenv()

# 阿里云百炼配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_MODEL = os.getenv("DASHSCOPE_MODEL", "qwen3-32b-ft-202604041221-e4a4o")
DASHSCOPE_FINETUNED_MODEL = os.getenv("DASHSCOPE_FINETUNED_MODEL", "qwen3-32b-ft-202604041221-e4a4o")

# 数据处理配置
DATA_SOURCE_DIR = os.getenv("DATA_SOURCE_DIR", "./data/raw")
DATA_OUTPUT_DIR = os.getenv("DATA_OUTPUT_DIR", "./data/processed")
MIN_TRAIN_SAMPLES = int(os.getenv("MIN_TRAIN_SAMPLES", "500"))

# 微信机器人配置
WECHAT_AUTO_REPLY = os.getenv("WECHAT_AUTO_REPLY", "false").lower() == "true"
WECHAT_REPLY_PREFIX = os.getenv("WECHAT_REPLY_PREFIX", "")
WECHAT_REPLY_SUFFIX = os.getenv("WECHAT_REPLY_SUFFIX", "")

# 微信号主信息 (从数据中自动提取)
OWNER_WXID = "wxid_9phvj8200vcv21"
OWNER_NAME = "Wei"