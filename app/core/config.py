from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    #basic
    PROJECT_NAME :str= "My FastAPI App"
    APP_ENV :str
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
    REDIS_HOST:str='localhost'
    REDIS_PORT :int=6379
    REDIS_PASSWORD :Optional[str] = None
    ELASTICSEARCH_HOST: str
    ES_AUTH:str
    ES_PASSWORD:str

    ES_SYNC_TIME:int

    #email
    SEND_ADDRESS: str
    EMAIL_AUTH_PASSWORD: str
    RECEIVE_ADDRESS: list
    SMTP_HOST: str
    SMTP_PORT:int

    # R2 配置
    R2_ACCESS_KEY_ID:str
    R2_SECRET_ACCESS_KEY:str
    R2_ENDPOINT_URL:str
    BUCKET_NAME:str
    # 公网访问域名 (在 R2 控制台绑定自己的域名或使用 dev 域名)
    PUBLIC_URL_PREFIX:str

    #上传文件类型校验
    ALLOWED_FILE_TYPES:list
    # 读取 .env 文件配置
    model_config = SettingsConfigDict(env_file="config_local.env",
                                      env_file_encoding='utf-8',
                                      extra='ignore' # 忽略环境变量中多余的字段
                                        )
    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


settings=Settings()