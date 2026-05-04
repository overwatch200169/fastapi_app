from datetime import datetime, timedelta, timezone
from typing import Annotated
from sqlmodel import Field, Session, SQLModel, create_engine, select
from fastapi import FastAPI, Depends, HTTPException, Query,status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from pydantic import BaseModel


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: str | None = None



# fake_users_db = {
#     "johndoe": {
#         "username": "johndoe",
#         "user_id": 0,
#
#         "password": "$argon2id$v=19$m=65536,t=3,p=4$wagCPXjifgvUFBzq4hqe3w$CYaIb8sB+wtD+Vu/P4uod1+Qof8h+1g7bbDlBID48Rc",
#         'level':0,
# 'disabled':False,
#     },
#     "alice": {
#         "username": "alice",
#
#         "user_id": 1,
#         "password": "fakehashedsecret2",
#         'level':1
#     },
# }

#
# class Item(SQLModel, table=True):
#     name:str = Field(index=True)
#     id:int | None = Field(default=None, primary_key=True)
#     price:int | None = Field(default=None, index=True)
#     description:str | None

class UserBase(SQLModel):
    username: str = Field(index=True)
    user_id: int | None = Field(default=None, primary_key=True)


class User(UserBase, table=True):

    email: str = Field(default=None, index=True, unique=True)
    password:str | None = Field(default=None, index=True)
    level:int | None
    # disabled:bool

class UserPublic(UserBase):
    user_id: int
    email : str
    username:str

class UserCreate(UserBase):
    email: str | None = Field(default=None, index=True)
    password: str | None
    level: int | None
    # disabled: bool


sqlite_file_name = "database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(sqlite_url, connect_args=connect_args)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
SessionDep = Annotated[Session, Depends(get_session)]

password_hash=PasswordHash.recommended()



app=FastAPI()

def verify_password(plain,hashed):
    return password_hash.verify(plain,hashed)

def get_password_hash(password: str):
    return password_hash.hash(password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


@app.get("/")
async def root():
    return {'message':'hello world'}


# def get_user_fake(db, username: str):
#     if username in db:
#         user_dict = db[username]
#         return User(**user_dict)

def get_user_from_db(email: str,session:SessionDep) ->User:
    result = session.exec(
        select(User).where(User.email == email)
    )
    user = result.first()
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    return user

# def Autenticate_user(fake_db,username:str,password:str):
#     user=get_user_fake(fake_db,username)
#     if not user:
#         return False
#     if not verify_password(password, user.password):
#         return False
#     return user
def authenticate_user(email:str, password:str, session:SessionDep):
    user = get_user_from_db(email,session)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user
def create_access_token(data:dict,expires_delta:timedelta|None=None):
    to_encode=data.copy()
    if expires_delta:
        expire=datetime.now(timezone.utc)+expires_delta
    else:
        expire=datetime.now(timezone.utc)+timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt



# def fake_decode_token(token):
#     user = get_user_fake(fake_users_db, token)
#     return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)],session:SessionDep):
    credentials_exception=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload=jwt.decode(token,SECRET_KEY,algorithms=[ALGORITHM])
        email=payload.get('sub')
        if email is None:
            raise credentials_exception
        token_data=TokenData(email=email)
    except InvalidTokenError:
        raise credentials_exception

    # user = get_user_fake(fake_users_db,username=token_data.username)
    user = get_user_from_db(token_data.email,session)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
)->UserPublic:
    # if current_user.disabled:
    #     raise HTTPException(status_code=400, detail="Inactive user")
    return UserPublic.model_validate(current_user)



@app.post('/token')
async def login_for_access_token(form_data:Annotated[OAuth2PasswordRequestForm,Depends()],session:SessionDep)->Token:
    user=authenticate_user(form_data.username,form_data.password,session)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password",headers={"WWW-Authenticate": "Bearer"},)
    access_token_expires=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token=create_access_token(data={"sub":user.email},expires_delta=access_token_expires)
    return Token(access_token=access_token,token_type='bearer')



@app.get("/users/me")
async def read_users_me(current_user: Annotated[UserPublic, Depends(get_current_active_user)]):
    return current_user
# @app.post("/items/")
# async def create_item(item:Item,session:SessionDep)->Item:
#     session.add(item)
#     session.commit()
#     session.refresh(item)
#
#     return item
#
#
# @app.get("/items/{item_id}")
# async def read_items(item_id:int,session:SessionDep):
#     item=session.get(Item,item_id)
#     if not item:
#         raise HTTPException(status_code=404, detail="item not found")
#
#     return item
#
# @app.delete("/items/{item_id}")
# async  def delete_item(item_id:int,session:SessionDep):
#     item = session.get(Item, item_id)
#     if not item:
#         raise HTTPException(status_code=404, detail="item not found")
#     session.delete(item)
#     session.commit()

@app.post("/users/",response_model=UserPublic)
async def create_user(user:UserCreate,session:SessionDep)->User:
    db_user=User.model_validate(user)

    hashed_password=get_password_hash(db_user.password)

    db_user.password=hashed_password
    session.add(db_user)

    session.commit()
    session.refresh(db_user)

    return db_user


#返回是列表，response_model 也要是列表
@app.get("/users",response_model=list[UserPublic])
async def read_users(session:SessionDep,offset: int = 0,
    limit: Annotated[int, Query(le=100)] = 100,):
    users=session.exec(select(User).offset(offset).limit(limit)).all()
    return users





@app.get("/users/{user_id}",response_model=UserPublic)
async def read_users(user_id:int,session:SessionDep):
    user=session.get(User,user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    return user

@app.delete("/users/{user_id}")
async  def delete_user(user_id:int,session:SessionDep):

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")
    session.delete(user)
    session.commit()