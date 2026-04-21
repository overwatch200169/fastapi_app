from sqlalchemy import QueuePool
from sqlmodel import Session, create_engine
from app.core.config import settings

# sqlite_file_name = "database.db"
# sqlite_url = f"sqlite:///./{sqlite_file_name}"
#
# connect_args = {"check_same_thread": False}
# engine = create_engine(settings.sqlite_url, connect_args=settings.connect_args)
#
#
#
#
# def get_session():
#     with Session(engine) as session:
#         yield session

engine=create_engine(settings.mysql_url,
                     echo=True,
                     poolclass=QueuePool,
                        pool_size=10,           # 连接池大小
                        max_overflow=20,        # 最大溢出连接
                        pool_timeout=30,        # 获取连接超时（秒）
                        pool_recycle=3600,      # 1小时回收连接
                        pool_pre_ping=True     #
                    )

def get_session():
    with Session(engine) as session:
        yield session

