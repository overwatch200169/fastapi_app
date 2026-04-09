from sqlmodel import Session, create_engine, SQLModel
from app.utils.config import settings

# sqlite_file_name = "database.db"
# sqlite_url = f"sqlite:///./{sqlite_file_name}"
#
# connect_args = {"check_same_thread": False}
engine = create_engine(settings.sqlite_url, connect_args=settings.connect_args)




def get_session():
    with Session(engine) as session:
        yield session

