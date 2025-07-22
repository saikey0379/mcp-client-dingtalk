from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

from app.logger import app_logger
from app.config import app_config, GenerateRDBUrl

from src.mcp.management import app_mcp_client
from src.mcp.service.mcp import NewMCPService

from src.user.io.user import NewClientUser
from src.user.service.user import NewServiceUser


class State():
    def __init__(self, logger, config, mcp_client):
        self.logger = logger
        self.config = config
        self.mcp_client = mcp_client
        self.rdb_session = None
        self.client_user = None
        self.service_user = None
        self.service_mcp = None
        self.service_card = None
        self.initialize()

    def initialize(self):
        self._initialize_rdb()
        self._initialize_service_user()
        self._initialize_service_mcp()

    def _initialize_rdb(self):
        Base = declarative_base()

        # 创建数据库连接
        engine = create_engine(GenerateRDBUrl(self.config.rdb))

        # 创建所有已定义的模型表示的表
        Base.metadata.create_all(engine)

        # 创建会话
        Session = sessionmaker(bind=engine)
        self.rdb_session = Session()

    def _initialize_service_user(self):
        self.client_user = NewClientUser(self.rdb_session)
        self.service_user = NewServiceUser(self.client_user)

    def _initialize_service_mcp(self):
        self.service_mcp = NewMCPService(
            self.logger, self.client_user, self.mcp_client, self.service_card)


app_state = State(
    app_logger.logger,
    app_config,
    app_mcp_client,
)
