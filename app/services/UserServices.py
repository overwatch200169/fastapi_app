from typing import Annotated, Tuple

from fastapi import Query, UploadFile
from sqlalchemy.orm.sync import update

from sqlmodel import Session, select

from app.core.file import upload_file
from app.models import User
from app.models.users import UserProfile
from app.schemas.users import UserCreate, UserProfilePublic, UserProfileUpdate

from app.core.security import get_password_hash


class UserService:
    def __init__(self,session:Session):
        self.session=session

    def create_user_with_profile(self,user:UserCreate)->User:
        db_user=User.model_validate(user)

        hashed_password=get_password_hash(db_user.password)

        db_user.password=hashed_password

        self.session.add(db_user)
        # self.session.refresh(db_user)
        self.session.flush()#立即提交并刷新操作，用于获取user_id

        db_profile=UserProfile(user_id=db_user.user_id)#用上面的写法写db_profile=UserProfile db_profile.user_id=db_user.user_id应该也行
        self.session.add(db_profile)
        self.session.commit()
        self.session.refresh(db_user)
        # self.session.refresh(db_profile)
        return db_user

    def list_users(self, offset: int = 0,limit: Annotated[int, Query(le=100)] = 100, ):
        session = self.session
        users = session.exec(select(User).offset(offset).limit(limit)).all()
        return users

    def read_user(self,user_id:int):
        session = self.session
        user=session.get(User,user_id)


        return user
    def delete_user(self,user_id:int):

        user = self.read_user(user_id)
        if not user:
            return False
        self.session.delete(user)
        self.session.commit()
        return True

    def read_user_profile(self,user_id:int):
        user_profile=self.session.get(UserProfile,user_id)
        if not user_profile:
            return False
        return user_profile

    def update_user_profile(self,user_id:int,profile:UserProfileUpdate):
        user_profile_db=self.read_user_profile(user_id)
        if not user_profile_db:
            return False
        profile_data=profile.model_dump(exclude_unset=True)
        #要model里有默认值才能发挥exclude_unset的作用
        user_profile_db.sqlmodel_update(profile_data)#self不用管
        self.session.add(user_profile_db)
        self.session.commit()
        self.session.refresh(user_profile_db)

        return user_profile_db

    def update_user_avatar(self,user,file:UploadFile):
        avatar_url=upload_file(file).get('filename')
        profile=UserProfileUpdate(avatar_url=avatar_url)
        updated_profile=self.update_user_profile(user.user_id,profile)
        return updated_profile

