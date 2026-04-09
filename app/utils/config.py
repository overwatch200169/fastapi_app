from pydantic.v1 import BaseSettings


class Settings(BaseSettings):
    #securty
    SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    #database
    sqlite_file_name = "database.db"
    sqlite_url = f"sqlite:///./{sqlite_file_name}"

    connect_args = {"check_same_thread": False}

settings=Settings()