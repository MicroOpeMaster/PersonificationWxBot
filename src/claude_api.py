"""
Claude API调用模块
使用 Anthropic SDK 调用 Claude API，支持从 skill 文件加载 persona
支持阿里云Anthropic兼容API
"""
import os
from pathlib import Path
from typing import Optional, Dict, List

try:
    import anthropic
except ImportError:
    anthropic = None

from src.config import ANTHROPIC_AUTH_TOKEN, ANTHROPIC_BASE_URL, ANTHROPIC_MODEL, SKILL_PATH


class ClaudeAPI:
    """Claude API封装（支持阿里云兼容API）"""

    def __init__(self, auth_token: str = None, base_url: str = None, model: str = None, skill_path: str = None):
        self.auth_token = auth_token or ANTHROPIC_AUTH_TOKEN
        self.base_url = base_url or ANTHROPIC_BASE_URL
        self.model = model or ANTHROPIC_MODEL
        self.skill_path = skill_path or SKILL_PATH

        if not self.auth_token:
            raise ValueError("请配置 ANTHROPIC_AUTH_TOKEN")

        if anthropic is None:
            raise ImportError("请安装 anthropic SDK: pip install anthropic")

        # 使用自定义 base_url（阿里云兼容API）
        self.client = anthropic.Anthropic(
            api_key=self.auth_token,
            base_url=self.base_url
        )
        self.system_prompt = self._load_skill(self.skill_path)

        print(f"Claude API 初始化成功")
        print(f"模型: {self.model}")
        print(f"Base URL: {self.base_url}")
        print(f"Skill路径: {self.skill_path}")

    def _load_skill(self, skill_path: str) -> str:
        """
        从 skill 目录加载 SKILL.md 作为 system prompt

        Args:
            skill_path: skill 目录路径

        Returns:
            system prompt 内容
        """
        skill_dir = Path(skill_path)

        if not skill_dir.exists():
            print(f"警告: Skill目录不存在 {skill_path}")
            return ""

        # 直接加载 SKILL.md 作为完整的 system prompt
        skill_file = skill_dir / "SKILL.md"
        if skill_file.exists():
            content = skill_file.read_text(encoding="utf-8")
            # 去除 YAML frontmatter (--- 开头的部分)
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    content = parts[2].strip()
            return content

        # 如果没有 SKILL.md，尝试加载 self.md + persona.md
        self_file = skill_dir / "self.md"
        persona_file = skill_dir / "persona.md"

        system_prompt = ""
        if self_file.exists():
            self_content = self_file.read_text(encoding="utf-8")
            system_prompt += f"# PART A: Self Memory\n\n{self_content}\n\n"
        if persona_file.exists():
            persona_content = persona_file.read_text(encoding="utf-8")
            system_prompt += f"# PART B: Persona\n\n{persona_content}"

        return system_prompt.strip()

    def chat(
        self,
        message: str,
        history: List[Dict] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024
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
        # 构建消息列表
        messages = []
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        messages.append({"role": "user", "content": message})

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=self.system_prompt,
                messages=messages,
                temperature=temperature
            )

            # 处理响应内容（GLM可能返回ThinkingBlock和TextBlock）
            # 优先查找text类型的块
            for block in response.content:
                if hasattr(block, 'type') and block.type == 'text':
                    # 强制去除换行符，确保回复是一行
                    return block.text.replace('\n', ' ').strip()

            # 备用方案：遍历所有块找有text属性的
            for block in response.content:
                if hasattr(block, 'text'):
                    return block.text.replace('\n', ' ').strip()

            # 最后尝试直接转字符串
            if response.content:
                return str(response.content[0]).replace('\n', ' ').strip()

            return None

        except anthropic.APIError as e:
            print(f"Claude API请求失败: {e}")
            return None
        except Exception as e:
            print(f"Claude API调用异常: {e}")
            return None

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
        messages = []
        if history:
            for msg in history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        messages.append({"role": "user", "content": message})

        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=1024,
                system=self.system_prompt,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield text

        except Exception as e:
            print(f"Claude流式API调用异常: {e}")


def test_api():
    """测试API连接"""
    api = ClaudeAPI()

    print("\n测试Claude API连接...")
    print(f"System prompt长度: {len(api.system_prompt)} 字符")

    response = api.chat("你好，请问你是谁？")

    if response:
        print(f"\nClaude回复: {response}")
        print("\nAPI连接正常!")
    else:
        print("API连接失败，请检查配置")


if __name__ == "__main__":
    test_api()