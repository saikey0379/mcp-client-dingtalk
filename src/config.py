# 导入 os 模块
import os
# 导入 yaml 模块
import yaml
# 导入 logging 模块
import logging
# 导入 argparse 模块
import argparse
# 导入 dotenv 模块
from dotenv import load_dotenv
# 加载 .env 文件
load_dotenv()

# 默认配置文件
DEFAULT_CONFIG_FILE = "config.yaml"

# 应用参数
AppArgs = None

# 应用配置
AppConfig = None

# 应用环境变量
AppEnv = None

# 参数类
class Args():
    # 初始化
    def __init__(self):
        # 配置
        self.config_file = None
        # 参数
        self.args = None

    # 初始化
    def initialize(self):
        # 获取参数
        self.args = self.get_args()

    # 获取参数
    def get_args(self):
        # 创建一个解析器对象
        parser = argparse.ArgumentParser(description='Process some parameters.')

        # 添加参数定义
        parser.add_argument('--config', type=str, help='Path to the configuration file')

        # 解析命令行参数
        args = parser.parse_args()

        # 如果配置文件为空
        if args.config is None:
            # 使用默认配置文件
            self.config_file = DEFAULT_CONFIG_FILE
        else:
            # 使用配置文件
            self.config_file = args.config

        # 返回参数
        return args
    
    # 获取配置文件
    def get_config_file(self):
        return self.config_file

# 获取参数
def GetArgs():
    # 定义参数全局变量
    global AppArgs
    # 如果参数为空
    if AppArgs is None:
        # 创建参数
        AppArgs = Args()
        # 初始化
        AppArgs.initialize()

    # 返回参数
    return AppArgs

# 配置类
class Config:
    # 初始化
    def __init__(self,config_file_path):
        # 配置文件路径
        self.config_file_path = config_file_path
        # 配置
        self.config = None
        # 初始化
        self.initialize()

    # 初始化
    def initialize(self):
        # 获取配置
        self.config = self.parse_yaml(self.config_file_path)

    # 解析 yaml 文件
    def parse_yaml(self,yaml_file_path):
        # 打开 yaml 文件
        with open(yaml_file_path, 'r') as file:
            try:
                # 解析 yaml 文件
                config = yaml.safe_load(file)
                # 返回配置
                return config
            except yaml.YAMLError as exc:
                # 打印错误
                logging.error(f"Error parsing YAML file: {exc}")
                # 返回 None
                return None
    
    # 获取配置
    def get_config(self):
        # 返回配置
        return self.config
    
# 获取配置
def GetConfig():
    # 定义配置全局变量
    global AppConfig
    # 如果配置为空
    if AppConfig is None:
        # 获取配置文件
        config_file_path = GetArgs().get_config_file()
        # 创建配置
        AppConfig = Config(config_file_path)

    # 返回配置
    return AppConfig

# 应用环境变量类
class Env:
    # 初始化
    def __init__(self):
        # 钉钉客户端 ID
        self.DINGTALK_CLIENT_ID = self.get_config_key("DINGTALK_CLIENT_ID")
        # 钉钉客户端密钥
        self.DINGTALK_CLIENT_SECRET = self.get_config_key("DINGTALK_CLIENT_SECRET")
        # AI 开放 AI API 密钥
        self.AI_OPENAI_API_KEY = self.get_config_key("AI_OPENAI_API_KEY")
        # AI 开放 AI API 基础 URL
        self.AI_OPENAI_API_BASE = self.get_config_key("AI_OPENAI_API_BASE")
        # MCP 服务器 URL
        self.MCP_SERVER_URL = self.get_config_key("MCP_SERVER_URL")

    # 获取配置键值
    def get_config_key(self,key):
        return os.getenv(key)

# 获取应用环境变量
def GetAppEnv():
    # 定义应用环境变量全局变量
    global AppEnv
    # 如果应用环境变量为空
    if AppEnv is None:
        # 创建应用环境变量
        AppEnv = Env()

    # 返回应用环境变量
    return AppEnv


