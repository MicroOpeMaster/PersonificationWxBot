"""
阿里云百炼API调用模块
支持模型微调后的推理调用
"""
import json
import requests
from typing import Optional, Dict, List
from src.config import DASHSCOPE_API_KEY, DASHSCOPE_MODEL, DASHSCOPE_FINETUNED_MODEL


class BailianAPI:
    """阿里云百炼API封装"""

    BASE_URL = "https://dashscope.aliyuncs.com/api/v1"

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or DASHSCOPE_API_KEY
        self.model = model or DASHSCOPE_FINETUNED_MODEL or DASHSCOPE_MODEL

        if not self.api_key:
            raise ValueError("请配置 DASHSCOPE_API_KEY")

    def chat(
        self,
        message: str,
        history: List[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 150
    ) -> Optional[str]:
        """
        发送聊天请求

        Args:
            message: 用户消息
            history: 对话历史 [{"role": "user/assistant", "content": "..."}]
            temperature: 温度参数 (0-1)
            max_tokens: 最大输出长度

        Returns:
            模型回复内容
        """
        messages = history or []
        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": temperature,
                "max_tokens": max_tokens,
                "result_format": "message",
                "enable_thinking": False
            }
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/services/aigc/text-generation/generation",
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                return result["output"]["choices"][0]["message"]["content"]
            else:
                print(f"API请求失败: {response.status_code} - {response.text}")
                return None

        except Exception as e:
            print(f"API调用异常: {e}")
            return None

    def chat_with_context(
        self,
        message: str,
        context_window: int = 5
    ) -> Optional[str]:
        """
        带上下文的聊天 (简化版，无历史记录管理)

        Args:
            message: 用户消息
            context_window: 上下文窗口大小

        Returns:
            模型回复内容
        """
        return self.chat(message, temperature=0.8, max_tokens=200)

    def stream_chat(
        self,
        message: str,
        history: List[Dict] = None
    ):
        """
        流式聊天 (实时返回)

        Args:
            message: 用户消息
            history: 对话历史

        Yields:
            增量回复内容
        """
        messages = history or []
        messages.append({"role": "user", "content": message})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-SSE": "enable"
        }

        payload = {
            "model": self.model,
            "input": {
                "messages": messages
            },
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 150,
                "result_format": "message",
                "incremental_output": True,
                "enable_thinking": False
            }
        }

        try:
            response = requests.post(
                f"{self.BASE_URL}/services/aigc/text-generation/generation",
                headers=headers,
                json=payload,
                stream=True,
                timeout=30
            )

            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data:'):
                        data = json.loads(line[5:])
                        if 'output' in data:
                            yield data['output']['choices'][0]['message']['content']

        except Exception as e:
            print(f"流式API调用异常: {e}")


class ChatHistoryManager:
    """对话历史管理"""

    def __init__(self, max_history: int = 10):
        self.max_history = max_history
        self.histories: Dict[str, List[Dict]] = {}

    def add_message(self, session_id: str, role: str, content: str):
        """添加消息到历史"""
        if session_id not in self.histories:
            self.histories[session_id] = []

        self.histories[session_id].append({
            "role": role,
            "content": content
        })

        # 保持历史长度
        if len(self.histories[session_id]) > self.max_history:
            self.histories[session_id] = self.histories[session_id][-self.max_history:]

    def get_history(self, session_id: str) -> List[Dict]:
        """获取对话历史"""
        return self.histories.get(session_id, [])

    def clear_history(self, session_id: str):
        """清空对话历史"""
        if session_id in self.histories:
            del self.histories[session_id]


def test_api():
    """测试API连接"""
    api = BailianAPI()

    print("测试百炼API连接...")
    response = api.chat("你好，请问你是谁？")

    if response:
        print(f"API响应: {response}")
        print("API连接正常!")
    else:
        print("API连接失败，请检查配置")


if __name__ == "__main__":
    test_api()