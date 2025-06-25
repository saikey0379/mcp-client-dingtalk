# mcp-client-dingtalk

  

一个用于钉钉机器人对话的mcp-cloud工具

  

## 1.钉钉卡片模版创建

#### 1.1.创建卡片模版

参考：
https://open.dingtalk.com/document/isvapp/card-template-building-and-publishing

#### 1.2.导入模版配置

模版路径：doc/dingtalk_card_call_tools.json

#### 1.3. 获取模版ID


## 2.启动服务

#### 2.1.配置环境变量


```shell
export RDB_HOST=xxxxxxx                                                                                                                                                                                                                    
export RDB_PORT=xxxxxxx                                                                                                                                                                                                                    
export RDB_USER=xxxxxxx                                                                                                                                                                                                                    
export RDB_PASSWORD=xxxxxxx                                                                                                                                                                                                                
export RDB_DATABASE=xxxxxxx                                                                                                                                                                                                                
export DINGTALK_CLIENT_ID=xxxxxxx                                                                                                                                                                                                          
export DINGTALK_CLIENT_SECRET=xxxxxxx                                                                                                                                                                                                      
export DINGTALK_CARD_TEMPLATE_ID_USER_CONFIG=xxxxxxx                                                                                                                                                                                       
export DINGTALK_CARD_TEMPLATE_ID_CALL_TOOLS=xxxxxxx                                                                                                                                                                                        
export MCP_SERVER_0_NAME=xxxxxxx                                                                                                                                                                                                           
export MCP_SERVER_0_URL=xxxxxxx
```


#### 2.2.安装Python

```bash

yum -y install python3-12

```

#### 2.3.安装Python依赖

```bash

pip install -r requirements.txt

```

#### 2.4. 启动

```bash

bash entrypoint.sh

```
## 3.DockerBuild
```bash
docker build -t mcp-client-dingtalk:release-1.1 .
```