#!/bin/bash

# 创建config.yaml文件
config=config.yaml

cat << EOF > $config
log:
  level: INFO

rdb:
  type: "postgresql"
  host: "$RDB_HOST"
  port: "$RDB_PORT"
  user: "$RDB_USER"
  password: "$RDB_PASSWORD"
  database: "$RDB_DATABASE"

dingtalk:
  type: "chatbot" # chatbot or ai_action
  client_id: "$DINGTALK_CLIENT_ID"
  client_secret: "$DINGTALK_CLIENT_SECRET"
  card_template_id_user_config: "$DINGTALK_CARD_TEMPLATE_ID_USER_CONFIG"
  card_template_id_call_tools: "$DINGTALK_CARD_TEMPLATE_ID_CALL_TOOLS"

mcp:
  mcpServers:
    $MCP_SERVER_0_NAME:
      url: "$MCP_SERVER_0_URL"
      disabled: false
      autoApprove: []
EOF

# 启动python main.py 并指定config.yaml文件
python main.py --config $config
