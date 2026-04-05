"""
工具模块
"""
from src.config import OWNER_WXID, OWNER_NAME


def get_owner_info() -> dict:
    """获取微信号主信息"""
    return {
        "wxid": OWNER_WXID,
        "name": OWNER_NAME
    }