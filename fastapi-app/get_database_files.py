from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import sqlite3
# from dotenv import load_dotenv
import os


#load env variables
# load_dotenv()



async def get_userdb_file():
    user_connection = sqlite3.connect('user_info.db')    #connect to metadata db
    return user_connection