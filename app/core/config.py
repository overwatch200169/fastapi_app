from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    #basic
    PROJECT_NAME :str= "My FastAPI App"
    APP_ENV :str= 'development'
    DEBUG :bool= True
    #securty
    SECRET_KEY :str
    ALGORITHM :str= "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 30
    REFRESH_TOKEN_EXPIRE :int= 7
    #database

    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "fastapi"

    connect_args :dict = {"check_same_thread": False}

    REDIS_PORT :int=6379
    ES_HOST: str = "https://localhost:9200"
    ES_AUTH:str
    ES_PASSWORD:str

    ES_SYNC_TIME:int

    #email
    SEND_ADDRESS: str
    EMAIL_AUTH_PASSWORD: str
    RECEIVE_ADDRESS: list
    SMTP_HOST: str
    SMTP_PORT:int

    # 读取 .env 文件配置
    model_config = SettingsConfigDict(env_file="config_local.env",
                                      env_file_encoding='utf-8',
                                      extra='ignore' # 忽略环境变量中多余的字段
                                        )
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings=Settings()