"""
数据分析脚本
分析训练数据的分布和质量
"""
import json
from pathlib import Path
from collections import Counter


def analyze_training_data(data_path: str):
    """分析训练数据"""
    data_file = Path(data_path)

    pairs = []
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            pairs.append(json.loads(line))

    print("=" * 50)
    print("训练数据分析报告")
    print("=" * 50)

    # 基本统计
    print(f"\n总训练数据对: {len(pairs)}")

    # 长度分布
    user_lengths = [len(p['messages'][0]['content']) for p in pairs]
    reply_lengths = [len(p['messages'][1]['content']) for p in pairs]

    print(f"\n用户消息长度:")
    print(f"  平均: {sum(user_lengths)/len(user_lengths):.1f}")
    print(f"  最短: {min(user_lengths)}")
    print(f"  最长: {max(user_lengths)}")

    print(f"\n回复长度:")
    print(f"  平均: {sum(reply_lengths)/len(reply_lengths):.1f}")
    print(f"  最短: {min(reply_lengths)}")
    print(f"  最长: {max(reply_lengths)}")

    # 短回复统计
    short_replies = [p for p in pairs if len(p['messages'][1]['content']) <= 5]
    print(f"\n短回复 (<=5字): {len(short_replies)} ({len(short_replies)/len(pairs)*100:.1f}%)")

    # 常见回复统计
    replies = [p['messages'][1]['content'] for p in pairs]
    reply_counter = Counter(replies)
    print(f"\n常见回复 (前20):")
    for reply, count in reply_counter.most_common(20):
        print(f"  '{reply}': {count}次")

    # 回复风格分析
    single_char = [p for p in pairs if len(p['messages'][1]['content']) == 1]
    print(f"\n单字回复: {len(single_char)} ({len(single_char)/len(pairs)*100:.1f}%)")

    # 建议
    print("\n" + "=" * 50)
    print("建议")
    print("=" * 50)

    if len(short_replies) / len(pairs) > 0.3:
        print("- 短回复比例较高，可考虑过滤过于简短的回复")

    if len(pairs) < 1000:
        print("- 数据量较少，建议增加更多聊天记录")
    elif len(pairs) >= 10000:
        print("- 数据量充足，适合进行模型微调")

    return pairs


if __name__ == "__main__":
    analyze_training_data("D:/code/AiWechat/data/processed/train_data.jsonl")