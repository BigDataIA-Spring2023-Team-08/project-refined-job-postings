from userdb import Base
from sqlalchemy import Column, Integer, String

class User_Table(Base):   #class to create schema for the table of users in db
    __tablename__ = "users"  
    
    id = Column(Integer, primary_key= True, index=True)
    name = Column(String)
    username = Column(String)
    password = Column(String)