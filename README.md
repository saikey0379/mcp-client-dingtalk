# mcp-client-dingtalk:一个用于钉钉机器人对话的mcp-cloud工具
## 配置环境变量

```shell
export DINGTALK_CLIENT_ID=xxxxxxxxxxxx
export DINGTALK_CLIENT_SECRET=xxxxxxxxxxxx
export AI_OPENAI_API_BASE=xxxxxxxxxxxx
export AI_OPENAI_API_KEY=xxxxxxxxxxxx
export MCP_SERVERS='{"mcpServers":{"mcp-server-0":{"url":"http://mcpserver.example.com/sse","disabled":false,"autoApprove":[]}}}'
```
## 启动

### 1.容器启动方式

```bash
bash docker/start.sh
```
### 2.命令行启动方式

#### 2.1.安装Python(version >= 3.12)

```bash
yum -y install python3-12
```
#### 2.2.安装依赖

```bash
pip install -r requirements.txt
```
#### 2.3. 启动

```bash
bash entrypoint.sh
```