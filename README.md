# AI聊天风格克隆

基于Claude Skill / 阿里云百炼微调模型  + uiautomation 实现的微信机器人。

> **推荐使用 Claude API + Skill 方式**：无需微调模型，通过 Skill 文件即可配置个性化回复风格，更灵活、更易维护。

## 架构

```
┌─────────────────┐   UIAutomation    ┌─────────────────┐
│  微信PC客户端    │◄────────────────►│  Python         │
│                 │                   │  (AI 服务)      │
│  消息收发       │                   │  百炼/Claude    │
└─────────────────┘                   └─────────────────┘
```

- **uiautomation**: 通过 Windows UI Automation API 控制微信PC客户端
- **Claude Skill（推荐）**: 调用 Claude API + Skill 文件，通过 prompt 配置人格，无需微调
- **百炼 API**: 调用阿里云百炼API，需要微调模型，适合固定风格场景

## 功能

- 实时监听微信消息
- 群聊：被@时自动回复（需配置白名单）
- 私聊：白名单联系人自动回复
- 支持两种AI模型：
  - 阿里云百炼微调模型
  - Claude API + Skill persona
- 支持前缀匹配触发
- 启动冷却期，避免回复历史消息

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
# 阿里云百炼（使用 --api bailian）
DASHSCOPE_API_KEY=你的API密钥
DASHSCOPE_MODEL=你的微调模型ID

# Claude API（使用 --api claude）
ANTHROPIC_AUTH_TOKEN=你的认证令牌
ANTHROPIC_BASE_URL=https://coding.dashscope.aliyuncs.com/apps/anthropic
ANTHROPIC_MODEL=glm-5
SKILL_PATH=D:\code\.claude\skills\自己

# 微信机器人配置
BOT_NAME=@你的微信名           # 群聊识别，必须带@
ALIAS_WHITELIST=好友1,好友2    # 私聊联系人白名单（逗号分隔）
ROOM_WHITELIST=群1,群2         # 群白名单（逗号分隔）
AUTO_REPLY_PREFIX=             # 回复前缀，留空则全部回复
STARTUP_COOLDOWN=5.0           # 启动冷却期（秒）
```

## 运行

1. 确保微信PC客户端已登录并保持窗口可见
2. 运行机器人：

```bash
# 使用阿里云百炼 API（默认）
python main.py --api bailian --mode auto

# 使用 Claude API + Skill
python main.py --api claude --mode auto

# 热键触发模式
python main.py --mode hotkey
```

参数说明：
- `--api`: 选择 API 类型
  - `bailian`: 阿里云百炼微调模型
  - `claude`: Claude API + Skill persona
- `--mode`: 运行模式
  - `auto`: 全自动监听回复
  - `hotkey`: 热键触发回复

## 自动回复逻辑

1. **群聊消息**：只有在白名单群内被 @ 时才回复
2. **私聊消息**：只有在白名单内的联系人才回复
3. **前缀匹配**：可设置 `AUTO_REPLY_PREFIX`，只有以此前缀开头的消息才触发

## 项目结构

```
AiWechat/
├── main.py                # 主入口
├── src/
│   ├── wxauto_bot.py      # 微信机器人核心模块
│   ├── auto_listener.py   # 全自动监听模块
│   ├── model_api.py       # 百炼 API
│   ├── claude_api.py      # Claude API + Skill
│   └── config.py          # 全局配置
├── scripts/
│   ├── process_data.py    # 数据处理
│   └── analyze_data.py    # 数据分析
├── data/
│   ├── raw/               # 原始数据
│   └── processed/         # 训练数据
└── requirements.txt       # Python 依赖
```

## Skill 文件结构

使用 Claude API 时，需要配置 Skill 目录（默认 `D:\code\.claude\skills\自己`）：

```
自己/
├── SKILL.md               # 完整的 persona 配置（主文件）
├── self.md                # 自我记忆
├── persona.md             # 性格定义
├── meta.json              # 元数据
└── memories/              # 记忆存储
```

代码会直接读取 `SKILL.md` 作为 system prompt，包含所有人格设定和运行规则。

## 创建个人数字镜像 Skill

可基于本项目导出的聊天记录，创建一个能像你一样说话的数字镜像 Skill。

参考：[yourself-skill](https://github.com/notdog1998/yourself-skill) — 从聊天记录蒸馏出你的数字分身

简要流程：
1. 用 [WeFlow](https://github.com/hicccc77/WeFlow) 导出微信聊天记录
2. 创建 Skill（基础信息 + 聊天记录分析）
3. 在 Claude Code 中通过 `/代号` 调用，扮演你进行对话

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