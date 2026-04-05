"""
阿里云百炼数据上传和模型微调脚本
"""
import os
import json
import time
import requests
from pathlib import Path
from tqdm import tqdm
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
BASE_URL = "https://dashscope.aliyuncs.com/api/v1"


def check_api_key():
    """检查API Key是否配置"""
    if not DASHSCOPE_API_KEY or DASHSCOPE_API_KEY == "your-api-key-here":
        print("错误: 请先配置 DASHSCOPE_API_KEY")
        print("1. 复制 .env.example 为 .env")
        print("2. 在 .env 中填写你的 API Key")
        print("\n获取API Key: https://bailian.console.aliyun.com/")
        return False
    return True


def upload_dataset(file_path: str, dataset_name: str = "wechat_chat_style") -> str:
    """
    上传数据集到百炼平台

    注意: 百炼平台的数据上传通常需要通过OSS或控制台
    此函数提供API方式的尝试
    """
    print(f"\n准备上传数据集: {file_path}")

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }

    # 检查文件
    data_file = Path(file_path)
    if not data_file.exists():
        print(f"错误: 文件不存在 {file_path}")
        return None

    file_size = data_file.stat().st_size
    print(f"文件大小: {file_size / 1024:.1f} KB")

    # 读取数据统计
    lines = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            lines.append(json.loads(line))
    print(f"数据条数: {len(lines)}")

    # 百炼数据集API
    # 文档: https://help.aliyun.com/zh/model-studio/developer-guide/create-a-dataset
    try:
        # 步骤1: 创建数据集
        create_payload = {
            "name": dataset_name,
            "type": "train",
            "dataType": "conversation",  # 对话类型数据
            "description": f"微信聊天风格数据集 - {len(lines)}条对话"
        }

        print("\n正在创建数据集...")
        response = requests.post(
            f"{BASE_URL}/datasets",
            headers=headers,
            json=create_payload
        )

        if response.status_code in [200, 201]:
            result = response.json()
            dataset_id = result.get("id") or result.get("data", {}).get("id")
            print(f"数据集创建成功! ID: {dataset_id}")
            return dataset_id
        else:
            print(f"API返回: {response.status_code}")
            print(f"响应: {response.text}")
            return None

    except Exception as e:
        print(f"上传异常: {e}")
        return None


def create_finetune_job(dataset_id: str, base_model: str = "qwen-turbo") -> str:
    """
    创建微调任务

    Args:
        dataset_id: 数据集ID
        base_model: 基础模型
    """
    print(f"\n创建微调任务...")
    print(f"基础模型: {base_model}")
    print(f"数据集ID: {dataset_id}")

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": base_model,
        "dataset_id": dataset_id,
        "hyperparameters": {
            "epochs": 3,
            "batch_size": 16,
            "learning_rate": 0.0001
        },
        "name": "wechat_style_clone"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/fine-tuning/jobs",
            headers=headers,
            json=payload
        )

        if response.status_code in [200, 201]:
            result = response.json()
            job_id = result.get("id") or result.get("data", {}).get("id")
            print(f"微调任务创建成功! ID: {job_id}")
            return job_id
        else:
            print(f"API返回: {response.status_code}")
            print(f"响应: {response.text}")
            return None

    except Exception as e:
        print(f"创建任务异常: {e}")
        return None


def check_job_status(job_id: str) -> dict:
    """查询微调任务状态"""
    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
    }

    try:
        response = requests.get(
            f"{BASE_URL}/fine-tuning/jobs/{job_id}",
            headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            print(f"查询失败: {response.status_code}")
            return None

    except Exception as e:
        print(f"查询异常: {e}")
        return None


def console_guide():
    """
    控制台操作指南
    当API方式不可用时，提供手动操作步骤
    """
    print("\n" + "=" * 60)
    print("阿里云百炼平台 - 手动操作指南")
    print("=" * 60)

    print("\n【步骤1】登录百炼平台")
    print("  访问: https://bailian.console.aliyun.com/")

    print("\n【步骤2】上传数据集")
    print("  1. 点击左侧菜单 '数据管理' -> '数据集'")
    print("  2. 点击 '创建数据集'")
    print("  3. 选择数据类型: '对话数据'")
    print("  4. 上传文件: D:/code/AiWechat/data/processed/train_data.jsonl")
    print("  5. 等待数据集验证完成")

    print("\n【步骤3】创建微调任务")
    print("  1. 点击左侧菜单 '模型微调'")
    print("  2. 点击 '创建训练任务'")
    print("  3. 选择基础模型: qwen-turbo (推荐)")
    print("  4. 选择数据集: 刚上传的数据集")
    print("  5. 配置参数:")
    print("     - 训练轮数: 3 (推荐)")
    print("     - 学习率: 默认即可")
    print("  6. 点击 '开始训练'")

    print("\n【步骤4】等待训练完成")
    print("  - 训练时间约 30分钟 - 2小时")
    print("  - 可在任务列表查看进度")

    print("\n【步骤5】部署模型")
    print("  1. 训练完成后，点击 '部署模型'")
    print("  2. 获取模型ID (格式如: qwen-xxx-finetuned-xxx)")
    print("  3. 将模型ID配置到 .env 文件")

    print("\n【数据文件路径】")
    data_path = "D:/code/AiWechat/data/processed/train_data.jsonl"
    print(f"  {data_path}")
    print(f"  数据条数: 25,899条")
    print(f"  文件大小: ~2.5MB")

    print("\n" + "=" * 60)


def test_api_connection():
    """测试API连接"""
    print("\n测试百炼API连接...")

    headers = {
        "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
        "Content-Type": "application/json"
    }

    # 测试基础模型调用
    payload = {
        "model": "qwen-turbo",
        "input": {
            "messages": [{"role": "user", "content": "你好"}]
        }
    }

    try:
        response = requests.post(
            f"{BASE_URL}/services/aigc/text-generation/generation",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            print("[OK] API连接成功!")
            return True
        else:
            print(f"[FAIL] API返回错误: {response.status_code}")
            print(f"  响应: {response.text[:200]}")
            return False

    except Exception as e:
        print(f"[FAIL] 连接异常: {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("阿里云百炼 - 数据上传和模型微调")
    print("=" * 60)

    if not check_api_key():
        console_guide()
        return

    # 测试API连接
    if not test_api_connection():
        console_guide()
        return

    # 尝试API上传
    data_path = "D:/code/AiWechat/data/processed/train_data.jsonl"

    print("\n尝试通过API上传数据集...")
    dataset_id = upload_dataset(data_path)

    if dataset_id:
        # 创建微调任务
        job_id = create_finetune_job(dataset_id)

        if job_id:
            print("\n训练任务已提交!")
            print(f"任务ID: {job_id}")
            print("\n正在查询任务状态...")

            status = check_job_status(job_id)
            if status:
                print(f"当前状态: {status.get('status', 'unknown')}")

            print("\n请定期查询任务状态，或登录控制台查看进度")
    else:
        print("\nAPI上传失败，请使用控制台手动操作")
        console_guide()


if __name__ == "__main__":
    main()