# MCP Client for DingTalk

一个基于 Model Context Protocol (MCP) 的钉钉机器人客户端，支持智能对话和工具调用功能。

## 🚀 功能特性

- **智能对话**: 支持与钉钉机器人进行自然语言对话
- **MCP 协议**: 基于 Model Context Protocol，支持多种 AI 模型
- **工具调用**: 支持调用各种 MCP 服务器提供的工具
- **卡片交互**: 使用钉钉卡片模板提供丰富的交互体验
- **用户管理**: 支持多用户配置和会话管理
- **健康检查**: 内置 MCP 服务器健康检查机制

## 📋 系统要求

- Python 3.12+
- PostgreSQL 数据库
- 钉钉开发者账号

## 🛠️ 安装部署

### 1. 环境准备

```bash
# 安装 Python 3.12
yum -y install python3-12

# 或使用其他包管理器
# Ubuntu/Debian: sudo apt-get install python3.12
# macOS: brew install python@3.12
```

### 2. 克隆项目

```bash
git clone <repository-url>
cd mcp-client-dingtalk
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
# 数据库配置
export RDB_HOST=your_postgresql_host
export RDB_PORT=5432
export RDB_USER=your_db_user
export RDB_PASSWORD=your_db_password
export RDB_DATABASE=your_db_name

# 钉钉配置
export DINGTALK_CLIENT_ID=your_dingtalk_client_id
export DINGTALK_CLIENT_SECRET=your_dingtalk_client_secret
export DINGTALK_CARD_TEMPLATE_ID_USER_CONFIG=your_user_config_template_id
export DINGTALK_CARD_TEMPLATE_ID_CALL_TOOLS=your_call_tools_template_id
export DINGTALK_CARD_TEMPLATE_ID_AI_RESULT=your_ai_result_template_id

# AI 配置
export AI_OPENAI_API_KEY=your_openai_api_key
export AI_OPENAI_API_BASE=https://api.openai.com/v1

# MCP 服务器配置
export MCP_SERVER_0_NAME=your_mcp_server_name
export MCP_SERVER_0_URL=your_mcp_server_url
```

### 5. 启动服务

```bash
bash entrypoint.sh
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t mcp-client-dingtalk:latest .
```

### 运行容器

```bash
docker run -d \
  --name mcp-client-dingtalk \
  -e RDB_HOST=your_postgresql_host \
  -e RDB_PORT=5432 \
  -e RDB_USER=your_db_user \
  -e RDB_PASSWORD=your_db_password \
  -e RDB_DATABASE=your_db_name \
  -e DINGTALK_CLIENT_ID=your_dingtalk_client_id \
  -e DINGTALK_CLIENT_SECRET=your_dingtalk_client_secret \
  -e DINGTALK_CARD_TEMPLATE_ID_USER_CONFIG=your_user_config_template_id \
  -e DINGTALK_CARD_TEMPLATE_ID_CALL_TOOLS=your_call_tools_template_id \
  -e DINGTALK_CARD_TEMPLATE_ID_AI_RESULT=your_ai_result_template_id \
  -e AI_OPENAI_API_KEY=your_openai_api_key \
  -e AI_OPENAI_API_BASE=https://api.openai.com/v1 \
  -e MCP_SERVER_0_NAME=your_mcp_server_name \
  -e MCP_SERVER_0_URL=your_mcp_server_url \
  mcp-client-dingtalk:latest
```

## ⚙️ 配置说明

### 钉钉卡片模板配置

1. **创建卡片模板**
   - 参考钉钉官方文档：https://open.dingtalk.com/document/isvapp/card-template-building-and-publishing

2. **导入模板配置**
   - 使用项目提供的模板配置：`doc/dingtalk_card_call_tools.json`

3. **获取模板ID**
   - 在钉钉开发者后台获取创建的卡片模板ID

### 配置文件结构

项目使用 YAML 格式的配置文件，结构如下：

```yaml
log:
  level: INFO

rdb:
  type: "postgresql"
  host: "your_host"
  port: "5432"
  user: "your_user"
  password: "your_password"
  database: "your_database"

dingtalk:
  type: "chatbot"
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  card_template_id_user_config: "your_template_id"
  card_template_id_call_tools: "your_template_id"
  card_template_id_ai_result: "your_template_id"

ai-keys:
  openai:
    api_key: "your_api_key"
    api_base: "https://api.openai.com/v1"

mcp:
  mcpServers:
    your_server_name:
      url: "your_server_url"
      disabled: false
      autoApprove: []
```

## 📁 项目结构

```
mcp-client-dingtalk/
├── app/                    # 应用核心模块
│   ├── config.py          # 配置管理
│   ├── const.py           # 常量定义
│   ├── logger.py          # 日志管理
│   └── state.py           # 状态管理
├── src/                   # 源代码
│   ├── ai_clients/        # AI 客户端
│   ├── dingtalk/          # 钉钉相关功能
│   ├── mcp/               # MCP 协议实现
│   ├── user/              # 用户管理
│   └── utils/             # 工具函数
├── doc/                   # 文档
├── docker/                # Docker 相关文件
├── main.py                # 主程序入口
├── entrypoint.sh          # 启动脚本
├── requirements.txt       # Python 依赖
└── README.md             # 项目说明
```

## 🔧 开发指南

### 添加新的 AI 提供商

1. 在 `src/ai_clients/io/` 目录下创建新的客户端类
2. 继承 `ClientAIBase` 基类
3. 在 `src/ai_clients/model/const.py` 中添加提供商常量
4. 在 `src/user/io/user.py` 的 `_new_client_io` 方法中添加新的 case

### 添加新的 MCP 服务器

1. 在配置文件的 `mcp.mcpServers` 部分添加新的服务器配置
2. 确保服务器支持 MCP 协议
3. 配置相应的权限和自动批准规则

## 📊 监控和日志

- **健康检查**: 访问 `/healthz` 端点检查服务状态
- **日志级别**: 可通过配置文件调整日志级别
- **MCP 健康检查**: 自动监控 MCP 服务器连接状态

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有疑问，请：

1. 查看 [Issues](../../issues) 页面
2. 创建新的 Issue 描述问题
3. 联系项目维护者

## 🔄 更新日志

### v0.1.0
- 初始版本发布
- 支持钉钉机器人对话
- 集成 MCP 协议
- 支持工具调用功能