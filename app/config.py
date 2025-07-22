import yaml
import argparse

from app.const import DEFAULT_CONFIG_FILE
from src.ai_clients.model.const import AI_PROVIDER_LIST

# 参数类


class Args():
    # 初始化
    def __init__(self):
        # 配置
        self.config_file = None
        # 参数
        self.args = self.get_args()

    # 获取参数
    def get_args(self):
        # 创建一个解析器对象
        parser = argparse.ArgumentParser(
            description='Process some parameters.')

        # 添加参数定义
        parser.add_argument('--config', type=str,
                            help='Path to the configuration file')

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


app_args = Args()

# 配置类


class Config:
    # 初始化
    def __init__(self, config_file_path):
        # 获取配置
        self.config = self.parse_yaml(config_file_path)
        self.log = None if "log" not in self.config else self.config["log"]
        self.rdb = None if "rdb" not in self.config else self.config["rdb"]
        self.ai_keys = None if "ai-keys" not in self.config else self.config["ai-keys"]
        self.mcp = None if "mcp" not in self.config else self.config["mcp"]
        self.dingtalk = None if "dingtalk" not in self.config else self.config["dingtalk"]

    # 解析 yaml 文件
    def parse_yaml(self, yaml_file_path):
        # 打开 yaml 文件
        with open(yaml_file_path, 'r') as file:
            try:
                # 解析 yaml 文件
                config = yaml.safe_load(file)
                # 返回配置
                return config
            except yaml.YAMLError as exc:
                raise Exception(f"Error parsing YAML file: {exc}")

    def check(self):
        # 检查rdb配置
        check_rdb_config, error_message = self._check_rdb_config()
        if not check_rdb_config:
            return check_rdb_config, error_message
        # 检查钉钉配置
        check_dingtalk_config, error_message = self._check_dingtalk_config()
        if not check_dingtalk_config:
            return check_dingtalk_config, error_message
        # 检查ai配置
        check_ai_config, error_message = self._check_ai_config()
        if not check_ai_config:
            return check_ai_config, error_message
        # 检查mcp配置
        check_mcp_server_config, error_message = self._check_mcp_server_config()
        if not check_mcp_server_config:
            return check_mcp_server_config, error_message
        return True, ""

    # 检查rdb配置
    def _check_rdb_config(self):
        # 检查配置
        if self.config["rdb"]["type"] == "":
            return False, "RDB type is not set"
        if self.config["rdb"]["host"] == "":
            return False, "RDB host is not set"
        if self.config["rdb"]["port"] == "":
            return False, "RDB port is not set"
        if self.config["rdb"]["user"] == "":
            return False, "RDB user is not set"
        if self.config["rdb"]["password"] == "":
            return False, "RDB password is not set"
        if self.config["rdb"]["database"] == "":
            return False, "RDB database is not set"
        return True, ""
    # 检查钉钉配置

    def _check_dingtalk_config(self):
        # 检查配置
        if self.config["dingtalk"]["client_id"] == "":
            return False, "DingTalk client_id is not set"
        if self.config["dingtalk"]["client_secret"] == "":
            return False, "DingTalk client_secret is not set"
        return True, ""

    # 检查 AI 客户端配置
    def _check_ai_config(self):
        # 遍历 AI 客户端
        for provider_name, ai_client_config in self.config["ai-keys"].items():
            if ai_client_config["api_key"] == "" or ai_client_config["api_base"] == "":
                return False, f"AI provider {provider_name} is not set"
            if provider_name not in AI_PROVIDER_LIST:
                return False, f"Unsupported AI provider: {provider_name}"
        return True, ""

    # 检查 MCP 服务器配置
    def _check_mcp_server_config(self):
        # 检查配置
        if self.config["mcp"]["mcpServers"] == "":
            return False, "MCP servers is not set"
        return True, ""


app_config = Config(app_args.config_file)

DEFAULT_PROVIDER_NAME = list(app_config.ai_keys.keys())[0] if app_config.ai_keys else None
DEFAULT_API_KEY = app_config.ai_keys[DEFAULT_PROVIDER_NAME]["api_key"] if app_config.ai_keys else None
DEFAULT_API_BASE = app_config.ai_keys[DEFAULT_PROVIDER_NAME]["api_base"] if app_config.ai_keys else None


def GenerateRDBUrl(rdb_config: dict):
    if rdb_config["type"] == "postgresql":
        return f"postgresql://{rdb_config['user']}:{rdb_config['password']}@{rdb_config['host']}:{rdb_config['port']}/{rdb_config['database']}"
    elif rdb_config["type"] == "mysql":
        return f"mysql+pymysql://{rdb_config['user']}:{rdb_config['password']}@{rdb_config['host']}:{rdb_config['port']}/{rdb_config['database']}"
    else:
        raise Exception(f"Unsupported database type: {rdb_config['type']}")

