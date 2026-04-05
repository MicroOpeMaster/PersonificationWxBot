"""
检查部署状态并测试微调模型
"""
import requests
import time
import sys

API_KEY = "REDACTED_API_KEY"
BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

headers = {"Authorization": f"Bearer {API_KEY}"}


def check_deployment_status():
    """检查部署状态"""
    response = requests.get(f"{BASE_URL}/deployments", headers=headers)
    data = response.json()

    deployments = data.get("output", {}).get("deployments", [])
    if deployments:
        return deployments[0]
    return None


def test_model(model_id):
    """测试模型"""
    response = requests.post(
        f"{BASE_URL}/services/aigc/text-generation/generation",
        headers=headers,
        json={
            "model": model_id,
            "input": {"messages": [{"role": "user", "content": "今天吃啥"}]},
            "parameters": {"temperature": 0.8, "max_tokens": 100}
        },
        timeout=30
    )
    return response


def main():
    print("=" * 50)
    print("检查微调模型部署状态")
    print("=" * 50)

    deployment = check_deployment_status()
    if not deployment:
        print("未找到部署任务")
        return

    model_id = deployment["deployed_model"]
    status = deployment["status"]

    print(f"模型名称: {deployment['name']}")
    print(f"模型ID: {model_id}")
    print(f"当前状态: {status}")

    if status == "RUNNING":
        print("\n部署已完成! 测试模型...")
        test_response = test_model(model_id)

        if test_response.status_code == 200:
            result = test_response.json()
            content = result.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"测试成功!")
            print(f"用户: 今天吃啥")
            print(f"模型回复: {content}")

            # 更新配置
            print(f"\n请将以下模型ID写入 .env 文件:")
            print(f"DASHSCOPE_FINETUNED_MODEL={model_id}")
        else:
            print(f"测试失败: {test_response.text}")

    elif status == "PENDING":
        print("\n部署仍在进行中，请稍后再试")
        print("运行此脚本检查状态: python scripts/check_deployment.py")

    else:
        print(f"\n部署状态异常: {status}")


if __name__ == "__main__":
    main()