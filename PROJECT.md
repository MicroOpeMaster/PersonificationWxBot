"""
微信聊天风格克隆项目
====================

功能说明:
1. 读取微信聊天记录JSON文件
2. 处理数据生成训练数据集
3. 上传到阿里云百炼进行模型微调
4. 接入微信实现自动回复

项目结构:
---------
wechat-ai-clone/
├── data/
│   ├── raw/              # 原始数据 (可选)
│   └── processed/        # 处理后的训练数据
│       └── train_data.jsonl
├── scripts/
│   ├── process_data.py   # 数据处理脚本
│   └── analyze_data.py   # 数据分析脚本
├── src/
│   ├── config.py         # 配置模块
│   ├── model_api.py      # 百炼API模块
│   ├── wechat_bot.py     # 微信机器人模块
│   └── utils.py          # 工具模块
├── requirements.txt      # 依赖列表
└── .env.example          # 配置示例

使用步骤:
---------
1. 安装依赖:
   pip install -r requirements.txt

2. 处理数据:
   python scripts/process_data.py

3. 分析数据:
   python scripts/analyze_data.py

4. 上传数据到百炼平台进行微调:
   - 登录阿里云百炼平台: https://bailian.console.aliyun.com/
   - 创建数据集，上传 train_data.jsonl
   - 选择基础模型 (如 qwen-turbo)
   - 配置训练参数，启动微调
   - 等待训练完成，获取模型ID

5. 配置环境变量:
   复制 .env.example 为 .env
   填写 API_KEY 和微调后的模型ID

6. 测试API:
   python src/model_api.py

7. 运行机器人:
   python src/wechat_bot.py --mock   # 测试模式
   python src/wechat_bot.py --real   # 真实微信

注意事项:
---------
- 微信自动回复有封号风险，建议使用小号测试
- 数据量建议至少500条，推荐3000+条
- 过滤敏感内容和过于简短的回复
"""