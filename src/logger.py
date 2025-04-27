# 导入日志
import logging
# 导入配置
from src.config import GetConfig

# 日志实例
AppLogger = None

# 日志类
class Logger:
    # 初始化
    def __init__(self):
        self.log_level = None
        self.logger = None

    # 设置日志
    def initialize(self):
        # 获取日志级别
        self.log_level = GetConfig().get_config()["log"]["level"]
        # 创建日志实例
        self.logger = logging.getLogger()
        # 设置日志处理器
        handler = logging.StreamHandler()
        # 设置日志格式
        handler.setFormatter(
            logging.Formatter('%(asctime)s %(levelname)-5s [%(filename)s:%(lineno)d] %(message)s '))
        # 添加处理器到日志
        self.logger.addHandler(handler)
        self.logger.setLevel(self.log_level)

    def logger(self):
        return self.logger
    
# 获取日志实例
def GetLogger():
    # 定义日志实例全局变量
    global AppLogger
    # 如果日志实例为空
    if AppLogger is None:
        # 创建日志实例
        AppLogger = Logger()
        # 初始化
        AppLogger.initialize()

    return AppLogger