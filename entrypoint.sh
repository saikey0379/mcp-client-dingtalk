#!/bin/bash

# 创建config.yaml文件
config=config.yaml

cat << EOF > $config
log:
  level: INFO

dingtalk:
  client_id: "$DINGTALK_CLIENT_ID"
  client_secret: "$DINGTALK_CLIENT_SECRET"

ai-keys:
  openai:
    api_key: "$AI_OPENAI_API_KEY"
    api_base: "$AI_OPENAI_API_BASE"

mcp:
  mcpServers: '$MCP_SERVERS'
EOF

# 启动python main.py 并指定config.yaml文件
python main.py --config $config
