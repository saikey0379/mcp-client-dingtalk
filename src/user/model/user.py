
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class User(Base):
    __tablename__ = 'mcp_users'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    user_name = Column(String)
    mobile = Column(String)
    provider_name = Column(String)
    model = Column(String)
    api_key = Column(String)
    base_url = Column(String)
    language = Column(String)
    role = Column(String)

    def get_user_id(self):
        return self.user_id

    def get_user_name(self):
        return self.user_name

    def get_provider_name(self):
        return self.provider_name

    def get_model(self):
        return self.model
