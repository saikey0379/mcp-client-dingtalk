#! /bin/bash

# 构建容器
docker build -t mcp-client-dingtalk .

# 启动容器
docker run -d --name mcp-client-dingtalk \
-e AI_OPENAI_API_KEY=${AI_OPENAI_API_KEY} \
-e AI_OPENAI_API_BASE=${AI_OPENAI_API_BASE} \
-e DINGTALK_CLIENT_ID=${DINGTALK_CLIENT_ID} \
-e DINGTALK_CLIENT_SECRET=${DINGTALK_CLIENT_SECRET} \
-e MCP_SERVERS=${MCP_SERVERS} \
mcp-client-dingtalk

