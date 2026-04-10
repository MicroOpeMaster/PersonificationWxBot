# AI聊天风格克隆

基于阿里云百炼微调模型 + uiautomation 实现的微信机器人。

## 架构

```
┌─────────────────┐   UIAutomation    ┌─────────────────┐
│  微信PC客户端    │◄────────────────►│  Python         │
│                 │                   │  (AI 服务)      │
│  消息收发       │                   │  百炼 API       │
└─────────────────┘                   └─────────────────┘
```

- **uiautomation**: 通过 Windows UI Automation API 控制微信PC客户端
- **Python**: 调用阿里云百炼API，生成风格化回复

## 功能

- 实时监听微信消息
- 群聊：被@时自动回复（需配置白名单）
- 私聊：白名单联系人自动回复
- 使用微调后的AI模型回复
- 支持前缀匹配触发

## 安装

```bash
pip install -r requirements.txt
```

## 配置

1. 复制配置文件
```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

2. 编辑 `.env` 填写配置
```env
# 阿里云百炼
DASHSCOPE_API_KEY=你的API密钥
DASHSCOPE_MODEL=你的微调模型ID

# 微信机器人配置
BOT_NAME=@你的微信名           # 群聊识别，必须带@
ALIAS_WHITELIST=好友1,好友2    # 私聊联系人白名单（逗号分隔）
ROOM_WHITELIST=群1,群2         # 群白名单（逗号分隔）
AUTO_REPLY_PREFIX=             # 回复前缀，留空则全部回复
```

## 运行

1. 确保微信PC客户端已登录并保持窗口可见
2. 运行机器人：
```bash
python main.py
```

## 自动回复逻辑

1. **群聊消息**：只有在白名单群内被 @ 时才回复
2. **私聊消息**：只有在白名单内的联系人才回复
3. **前缀匹配**：可设置 `AUTO_REPLY_PREFIX`，只有以此前缀开头的消息才触发

## 项目结构

```
PersonificationWxBot/
├── main.py                # 主入口
├── src/
│   ├── wxauto_bot.py      # 微信机器人核心模块
│   ├── model_api.py       # 百炼 API
│   └── config.py          # 全局配置
├── scripts/
│   ├── process_data.py    # 数据处理
│   └── analyze_data.py    # 数据分析
├── data/
│   ├── raw/               # 原始数据
│   └── processed/         # 训练数据
└── requirements.txt       # Python 依赖
```

## 模型微调

1. 使用 [WeFlow](https://github.com/hicccc77/WeFlow) 导出微信聊天记录到 `data/raw/`
2. 运行数据处理脚本：
```bash
python scripts/process_data.py
```
3. 上传 `data/processed/train_data.jsonl` 到阿里云百炼平台
4. 创建微调任务，获取模型ID

## 注意事项

- 微信自动回复有封号风险，建议使用小号测试
- wxauto 需要 Windows 系统和微信PC客户端
- 微信客户端窗口需要保持可见状态
- 参考: [uiautomation](https://github.com/yinkaisheng/Python-UIAutomation-for-Windows)

## License

MIT