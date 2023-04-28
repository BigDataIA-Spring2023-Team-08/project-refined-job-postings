import pandas as pd
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
import sqlite3
from sqlite3 import Connection
import schema, userdb, db_model, oauth2
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from get_database_files import get_userdb_file
from hashing import Hash
from s3 import upload_to_s3, check_resume_on_s3
import uuid
import time 
from io import BytesIO
import os
import boto3
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from io import StringIO

router = APIRouter(
    prefix="/user",
    tags = ['Users']
)

get_db = userdb.get_db

@router.post('/create', response_model= schema.ShowUser)
def create_user(request: schema.User, db: Session = Depends(get_db)):
    """Creates a User in the User_Table inside the SQLite DB. The function stores the Name, Username and
        hashed password in the table to maintain privacy of the user.
    -----
    Input parameters:
    file_name : str
        string containg the filename (including extensions, if any) to fetch URL for
    Session : db
        current session of db
    -----
    Returns:
    new_user : db
        new user entry in the User_Table of the database
    """

    #authenticate S3 client for logging with your user credentials that are stored in your .env config file
    clientLogs = boto3.client('logs',
                            region_name='us-east-1',
                            aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                            aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                            )

    user = db.query(db_model.User_Table).filter(db_model.User_Table.username == request.username).first()  #query to db to match usernames
    if not user:
        new_user = db_model.User_Table(name = request.name, username = request.username, password = Hash.bcrypt(request.password), user_type = request.user_type) #creates a new user 
        # new_user = db_model.User_Table(name = request.name, username = request.username, password = Hash.bcrypt(request.password), resume_file= request.resume_filename, ) #creates a new user 
        db.add(new_user) 
        db.commit()
        db.refresh(new_user) #new user in the existing table
        
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/create Response: 200 Success"
                    }
                ]
        )

        return new_user
        #raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Invalid Credentials") 

    else:

        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/create Response: 400 User already exists"
                    }
                ]
        )

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "User already exists, please login")

@router.patch('/update',response_model= schema.ShowUser)
def update_password(username : str, new_password: schema.UpdateUserPassword, db: Session = Depends(get_db)):
    """ Function to change the user password and store the hashed password in the db
    Input parameters:
    username : str
        string containing the username of the user that requires a password update
    new_password : class 
        instance of a class containing the UserUpdatePassword
    
    -----
    Returns:
    user_in_db : db
        updates the user in the User_Table of the database
    """

    #authenticate S3 client for logging with your user credentials that are stored in your .env config file
    clientLogs = boto3.client('logs',
                            region_name='us-east-1',
                            aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                            aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                            )

    user_in_db = db.query(db_model.User_Table).filter(username == db_model.User_Table.username).first()
    if not user_in_db:

        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/update Response: 404 User not found"
                    }
                ]
        )

        raise HTTPException(status_code=404, detail="User not found")

    updated_user_data = dict(username = username, password = Hash.bcrypt(new_password.password)) #dictionary to store the user and hashes the new password
    for key, value in updated_user_data.items(): 
            setattr(user_in_db, key, value) #set attributes of user based on their username and new password
    db.add(user_in_db)
    db.commit()
    db.refresh(user_in_db)

    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/update Response: 200 Success"
                    }
                ]
        )

    return user_in_db

@router.get('/details', status_code=status.HTTP_200_OK)
async def user_details(username : str, db: Session = Depends(get_db), current_user: schema.User = Depends(oauth2.get_current_user), userdb_conn : Connection = Depends(get_userdb_file)):
    """Function to get user plan of the given username by accessing it through the user database
    -----
    Input parameters:
    username : str
        User name of currnet logged in user
    -----
    Returns:
    A string containing the user"""

     #authenticate S3 client for logging with your user credentials that are stored in your .env config file
    clientLogs = boto3.client('logs',
                            region_name='us-east-1',
                            aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                            aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                            )

    query = "SELECT user_type FROM users WHERE username==\'" + username +"\'"  #sql query to execute
    df_user = pd.read_sql_query(query, userdb_conn)
    
    if df_user['user_type'].to_list() == ['admin']:
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/details Response: 200 Success"
                    }
                ]
        )
        return 'admin'
    
    elif df_user['user_type'].to_list() == ['user']:
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/details Response: 200 Success"
                    }
                ]
        )
        return 'user'
    else:
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/details Response: 404 Success"
                    }
                ]
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "User not found")

@router.post('/uploadfile', status_code=status.HTTP_200_OK)
async def upload_file(username: str, file: UploadFile, db: Session = Depends(get_db), current_user: schema.User = Depends(oauth2.get_current_user)):
    """ Function to upload resume of the user to S3 bucket
    Input parameters:
    username : str
         The username of the user whose resume file name will be updated.
    file : UploadFile
        The uploaded file.
    -----
    Returns:
    filename : str
        The file name.
    """

    #authenticate S3 client for logging with your user credentials that are stored in your .env config file
    clientLogs = boto3.client('logs',
                            region_name='us-east-1',
                            aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                            aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                            )

    # generate filename with "resume_{username}"
    filename = f"resume_{username}.docx"

    # store the file on S3
    upload_to_s3(file, filename)
    user = db.query(db_model.User_Table).filter(db_model.User_Table.username == username).first()

    # update resume_filename field
    user.resume_file = filename

    # commit changes to database
    db.add(user)
    db.commit()

    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/uploadfile Response: 200 Success"
                    }
                ]
        )

    return {"filename": filename}

@router.get('/checkresume', status_code=status.HTTP_200_OK)
async def check_resume_file(username: str, db: Session = Depends(get_db), current_user: schema.User = Depends(oauth2.get_current_user)):
    """ Function to change the user password and store the hashed password in the db
    Input parameters:
    username : str
         The username of the user whose resume file name will be updated.
    file : UploadFile
        The uploaded file.
    -----
    Returns:
    filename : dict
        A dictionary containing the filename of the uploaded file.
    """

    #authenticate S3 client for logging with your user credentials that are stored in your .env config file
    clientLogs = boto3.client('logs',
                            region_name='us-east-1',
                            aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                            aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                            )

    # this is the default resume name for each user's resume that is uploaded on S3"
    filename = f"resume_{username}.docx"

    # store the file on S3
    check = check_resume_on_s3(username, filename)
    if check:

        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/checkresume Response: 200 Success"
                    }
                ]
        )

        return filename
    else: 

        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /user/checkresume Response: 404 User resume not uploaded"
                    }
                ]
        )

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "User resume not uploaded")
