from .users import User,UserProfile
from .articles import Article
#不需要被init包含只要继承了sqlmodel就可以被创建
__all__ = ["User","UserProfile",'Article']