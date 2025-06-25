# 导入日志
import logging

# 导入配置
from app.config import appConfig
# 导入常量
from app.const import DEFAULT_LOG_LEVEL, DEFAULT_LOG_FORMATTER

# 日志类


class Logger:
    # 初始化
    def __init__(self, config):
        self.log_level = DEFAULT_LOG_LEVEL
        self.logger = None
        self.uvicorn_logger_config = self._generate_uvicorn_logger_config()
        self.initialize(config)

    # 设置日志
    def initialize(self, config):
        # 获取日志级别
        if config["level"] is not None:
            self.log_level = config["level"]
        # 创建日志实例
        self.logger = logging.getLogger()
        # 设置日志处理器
        handler = logging.StreamHandler()
        # 设置日志格式
        handler.setFormatter(logging.Formatter(DEFAULT_LOG_FORMATTER))
        # 添加处理器到日志
        self.logger.addHandler(handler)
        self.logger.setLevel(self.log_level)

    def _generate_uvicorn_logger_config(self):
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": "%(levelprefix)s %(message)s",
                    "use_colors": None,
                },
                "access": {
                    "()": "uvicorn.logging.AccessFormatter",
                    "fmt": DEFAULT_LOG_FORMATTER,
                },
            },
            "handlers": {
                "access": {
                    "formatter": "access",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "uvicorn.error": {"level": self.log_level},
                "uvicorn.access": {"handlers": ["access"], "level": self.log_level, "propagate": False},
            },
        }


appLogger = Logger(appConfig.config["log"])
