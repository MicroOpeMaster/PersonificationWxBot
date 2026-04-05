"""
数据处理脚本
将微信聊天记录JSON转换为阿里云百炼微调格式(JSONL)
"""
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from tqdm import tqdm
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DATA_SOURCE_DIR, DATA_OUTPUT_DIR, OWNER_WXID


class ChatDataProcessor:
    """聊天数据处理类"""

    def __init__(self, source_dir: str, output_dir: str):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 统计信息
        self.stats = {
            "total_files": 0,
            "total_messages": 0,
            "text_messages": 0,
            "train_pairs": 0,
            "skipped_files": []
        }

    def load_json_file(self, file_path: Path) -> Dict:
        """加载JSON文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载文件失败 {file_path}: {e}")
            return None

    def filter_text_messages(self, messages: List[Dict]) -> List[Dict]:
        """过滤只保留文本消息"""
        text_msgs = []
        for msg in messages:
            # 只保留文本消息
            if msg.get("type") == "文本消息" and msg.get("content"):
                text_msgs.append(msg)
        return text_msgs

    def merge_consecutive_messages(self, messages: List[Dict], max_gap_seconds: int = 60) -> List[Dict]:
        """
        合并同一人连续发送的消息
        将短时间内同一人的多条消息合并为一条
        """
        if not messages:
            return []

        merged = []
        current_msg = None

        for msg in messages:
            if current_msg is None:
                current_msg = {
                    "isSend": msg["isSend"],
                    "content": msg["content"],
                    "createTime": msg["createTime"],
                    "senderUsername": msg["senderUsername"]
                }
            elif (msg["isSend"] == current_msg["isSend"] and
                  msg["senderUsername"] == current_msg["senderUsername"] and
                  msg["createTime"] - current_msg["createTime"] <= max_gap_seconds):
                # 合并消息
                current_msg["content"] += "\n" + msg["content"]
                current_msg["createTime"] = msg["createTime"]
            else:
                merged.append(current_msg)
                current_msg = {
                    "isSend": msg["isSend"],
                    "content": msg["content"],
                    "createTime": msg["createTime"],
                    "senderUsername": msg["senderUsername"]
                }

        if current_msg:
            merged.append(current_msg)

        return merged

    def create_training_pairs(self, messages: List[Dict], owner_wxid: str) -> List[Dict]:
        """
        创建训练数据对
        格式: 对方说的话 -> 微信号主的回复
        """
        pairs = []

        for i in range(len(messages) - 1):
            current = messages[i]
            next_msg = messages[i + 1]

            # 对方发消息 -> 号主回复
            if current["isSend"] == 0 and next_msg["isSend"] == 1:
                content = current["content"].strip()
                reply = next_msg["content"].strip()

                # 过滤太短或太长的内容
                if len(content) >= 1 and len(content) <= 500 and len(reply) >= 1 and len(reply) <= 500:
                    pairs.append({
                        "messages": [
                            {"role": "user", "content": content},
                            {"role": "assistant", "content": reply}
                        ]
                    })

        return pairs

    def process_single_file(self, file_path: Path, owner_wxid: str) -> Tuple[List[Dict], Dict]:
        """处理单个JSON文件"""
        data = self.load_json_file(file_path)
        if not data:
            return [], {"skipped": True, "reason": "无法加载文件"}

        session = data.get("session", {})
        messages = data.get("messages", [])

        # 只处理私聊
        if session.get("type") != "私聊":
            return [], {"skipped": True, "reason": "非私聊数据"}

        file_stats = {
            "file": file_path.name,
            "contact": session.get("remark") or session.get("displayName"),
            "total_messages": len(messages),
            "skipped": False
        }

        # 过滤文本消息
        text_messages = self.filter_text_messages(messages)
        file_stats["text_messages"] = len(text_messages)

        if len(text_messages) < 10:
            return [], {"skipped": True, "reason": "消息数量太少"}

        # 合并连续消息
        merged_messages = self.merge_consecutive_messages(text_messages)
        file_stats["merged_messages"] = len(merged_messages)

        # 创建训练对
        pairs = self.create_training_pairs(merged_messages, owner_wxid)
        file_stats["train_pairs"] = len(pairs)

        return pairs, file_stats

    def process_all_files(self, owner_wxid: str = OWNER_WXID) -> List[Dict]:
        """处理所有JSON文件"""
        all_pairs = []
        json_files = list(self.source_dir.glob("*.json"))

        # 过滤只处理私聊文件
        private_chat_files = [f for f in json_files if f.name.startswith("私聊_")]

        print(f"找到 {len(private_chat_files)} 个私聊文件")

        for file_path in tqdm(private_chat_files, desc="处理文件"):
            pairs, stats = self.process_single_file(file_path, owner_wxid)

            self.stats["total_files"] += 1
            self.stats["total_messages"] += stats.get("total_messages", 0)
            self.stats["text_messages"] += stats.get("text_messages", 0)

            if stats.get("skipped"):
                self.stats["skipped_files"].append({
                    "file": file_path.name,
                    "reason": stats.get("reason")
                })
            else:
                all_pairs.extend(pairs)
                self.stats["train_pairs"] += len(pairs)

        return all_pairs

    def save_training_data(self, pairs: List[Dict], output_file: str = "train_data.jsonl"):
        """保存训练数据为JSONL格式"""
        output_path = self.output_dir / output_file

        with open(output_path, 'w', encoding='utf-8') as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + '\n')

        print(f"训练数据已保存到: {output_path}")
        return output_path

    def print_stats(self):
        """打印统计信息"""
        print("\n" + "=" * 50)
        print("数据处理统计")
        print("=" * 50)
        print(f"处理文件数: {self.stats['total_files']}")
        print(f"总消息数: {self.stats['total_messages']}")
        print(f"文本消息数: {self.stats['text_messages']}")
        print(f"训练数据对: {self.stats['train_pairs']}")
        print(f"跳过文件数: {len(self.stats['skipped_files'])}")

        if self.stats['skipped_files']:
            print("\n跳过的文件:")
            for item in self.stats['skipped_files'][:5]:
                print(f"  - {item['file']}: {item['reason']}")


def main():
    """主函数"""
    processor = ChatDataProcessor(DATA_SOURCE_DIR, DATA_OUTPUT_DIR)

    print("开始处理聊天数据...")
    pairs = processor.process_all_files()

    if pairs:
        processor.save_training_data(pairs)
        processor.print_stats()

        # 按对话数量排序，显示最多的几个联系人
        print("\n" + "=" * 50)
        print("训练数据示例 (前5条):")
        print("=" * 50)
        for i, pair in enumerate(pairs[:5]):
            print(f"\n[{i+1}]")
            print(f"用户: {pair['messages'][0]['content']}")
            print(f"回复: {pair['messages'][1]['content']}")
    else:
        print("未生成任何训练数据")


if __name__ == "__main__":
    main()