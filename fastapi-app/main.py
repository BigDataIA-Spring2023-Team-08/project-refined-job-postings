import sqlite3
import os
# import boto3
import pandas as pd
import db_model
from fastapi import FastAPI, APIRouter, status, HTTPException, Depends
# from dotenv import load_dotenv
from sqlite3 import Connection
from get_database_files import get_userdb_file
from userdb import engine
from routers import user, authentication

#load env variables
# load_dotenv()

app2 = FastAPI()     #create fastapi object

db_model.Base.metadata.create_all(bind = engine) #create all tables stored in db if not present

#add all routers
app2.include_router(user.router)
app2.include_router(authentication.router)
