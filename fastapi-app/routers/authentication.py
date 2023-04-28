from http.client import HTTPException
from fastapi import APIRouter, Depends, status,HTTPException
from pytest import Session
from hashing import Hash
import schema, db_model,userdb, jwttoken
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
import boto3
import os
import time

router = APIRouter(
    tags=["Authentication"]
)


@router.post('/login')
def login(request: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(userdb.get_db)):
    """Function to query username and password from the SQLite database to verify Users during
        login and generate JWT Token for the session. Raises 404 Exception if the credentials dont match
    -----
    Input parameters:
    OAuth2PasswordRequestForm : class
        class dependency containing user and password form
    Session : db
        current session of db
    -----
    Returns:
    A string containing the JWT access token and throws a HTTP_404_NOT_FOUND exception in case of error in username/password
    """

    #authenticate S3 client for logging with your user credentials that are stored in your .env config file
    clientLogs = boto3.client('logs',
                            region_name='us-east-1',
                            aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                            aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                            )

    user = db.query(db_model.User_Table).filter(db_model.User_Table.username == request.username).first()  #query to db to match usernames
    if not user:
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /login Response: 404 Invalid login"
                    }
                ]
        )
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Invalid Credentials") 

    if not Hash.verify(user.password, request.password):
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /login Response: 404 Invalid login"
                    }
                ]
        )
        raise HTTPException(status_code = status.HTTP_404_NOT_FOUND, detail="Incorrect Password")  #verify hashed password with plain text

    #generate JWT Token
    access_token = jwttoken.create_access_token(data={"sub": user.name})  #generate access token
    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /login Response: 200 Success"
                    }
                ]
        )
    return {"access_token": access_token, "token_type": "bearer"}