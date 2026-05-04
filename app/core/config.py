from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    #securty
    SECRET_KEY :str
    ALGORITHM :str= "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES:int = 30
    REFRESH_TOKEN_EXPIRE :int= 7
    #database
    # sqlite_file_name = "database.db"
    # sqlite_url = f"sqlite:///./{sqlite_file_name}"
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "password"
    MYSQL_HOST: str = "127.0.0.1"
    MYSQL_PORT: int = 3306
    MYSQL_DB: str = "fastapi"
    # mysql_url = "mysql+pymysql://root:root@127.0.0.1:3306/fastapi?charset=utf8mb4"

    connect_args :dict = {"check_same_thread": False}

    REDIS_PORT :int=6379
    ES_HOST: str = "http://localhost:9200"

    #email
    SEND_ADDRESS: str ='overvatch200019@163.com'
    EMAIL_AUTH_PASSWORD: str
    RECEIVE_ADDRESS: list =['1091587398@qq.com']
    SMTP_HOST: str ='smtp.163.com'

    # 读取 .env 文件配置
    model_config = SettingsConfigDict(env_file="config_local.env",
                                      env_file_encoding='utf-8',
                                      extra='ignore' # 忽略环境变量中多余的字段
                                        )


settings=Settings()