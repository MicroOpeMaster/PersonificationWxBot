# 微信AI聊天风格克隆机器人

基于阿里云百炼微调模型，实现微信消息自动监听和智能回复。

## 功能

- 扫描微信聊天记录，训练个性化AI模型
- 自动监听微信私聊消息
- 使用微调后的模型智能回复
- 支持上下文对话历史

## 安装

```bash
# 克隆项目
git clone https://github.com/your-username/AiWechat.git
cd AiWechat

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

## 配置

1. 复制配置文件
```bash
copy .env.example .env
```

2. 编辑 `.env` 填写配置
```
DASHSCOPE_API_KEY=你的API密钥
DASHSCOPE_MODEL=你的微调模型ID
```

3. 微信客户端版本要求
- 需要 **3.9.11.17** 版本的微信PC客户端
- 下载地址：https://github.com/tom-snow/wechat-windows-versions/releases/download/v3.9.12.57/WeChatSetup-3.9.12.57.exe

## 运行

```bash
# 自动监听所有私聊
python wxauto_bot.py --run

# 监听模式（最多5个会话）
python wxauto_bot.py --listen

# 交互模式
python wxauto_bot.py --interactive

# 测试发送
python wxauto_bot.py --test
```

## 项目结构

```
AiWechat/
├── wxauto_bot.py      # 主机器人程序
├── main_bot.py        # itchat版本（网页版微信）
├── simple_bot.py      # 简单交互版本
├── src/
│   ├── config.py      # 配置模块
│   ├── model_api.py   # API调用模块
│   └── utils.py       # 工具模块
├── scripts/
│   ├── process_data.py    # 数据处理
│   └── analyze_data.py    # 数据分析
├── data/
│   ├── raw/           # 原始数据
│   └── processed/     # 处理后的训练数据
├── .env.example       # 配置示例
├── requirements.txt   # 依赖列表
└── start.bat          # Windows启动脚本
```

## 模型微调

1. 准备聊天记录数据（JSON格式）
2. 运行数据处理脚本
```bash
python scripts/process_data.py
```
3. 上传 `data/processed/train_data.jsonl` 到阿里云百炼平台
4. 创建微调任务，获取模型ID

## 注意事项

- 微信自动回复有封号风险，建议使用小号测试
- itchat版本依赖网页版微信，部分账号无法登录
- wxauto版本需要特定微信客户端版本

## License

MIT