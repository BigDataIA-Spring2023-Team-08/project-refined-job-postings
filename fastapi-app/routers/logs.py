import os
import boto3
import time
import pandas as pd
from datetime import datetime, timedelta
import requests
import sqlite3
from sqlite3 import Connection
import schema, userdb, db_model, oauth2
from fastapi import FastAPI, APIRouter, status, HTTPException, Depends
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm
from get_database_files import get_userdb_file
from dotenv import load_dotenv

#load env variables
load_dotenv()

#create router object
router = APIRouter(
    prefix="/logs",
    tags=['logs']
)


# get_db = userdb.get_db

@router.get('/admin', status_code=status.HTTP_200_OK)
async def get_admin_logs(username : str, current_user: schema.User = Depends(oauth2.get_current_user)):

    #define the log client
    clientLogs = boto3.client('logs',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                        )

    if username != 'admin':
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                    logGroupName = "project-refined-job-postings",
                    logStreamName = "api",
                    logEvents = [
                        {
                        'timestamp' : int(time.time() * 1e3),
                        'message' : "API endpoint: /logs/admin Response: 400 Error"
                        }
                    ]
            )

        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Non admin user requesting dashboard access")
    else:
        #define log group and stream names
        log_group_name = 'project-refined-job-postings'
        log_stream_name = 'api'
        query = f"fields @timestamp, @message | sort @timestamp asc | filter @logStream='{log_stream_name}'" #define a log query to get the required logs from the given log stream
        response = clientLogs.start_query(
            logGroupName=log_group_name,
            startTime=0,
            endTime=int(time.time() * 1000),
            queryString=query,
            limit=10000
        )
        #wait for query to complete
        query_id = response['queryId']
        response = None
        while response is None or response['status'] == 'Running':
            print('Waiting for query to complete...')
            time.sleep(1)
            response = clientLogs.get_query_results(    #get all logs
                queryId=query_id
            )
        if response == None:
            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                    logGroupName = "project-refined-job-postings",
                    logStreamName = "api",
                    logEvents = [
                        {
                        'timestamp' : int(time.time() * 1e3),
                        'message' : "API endpoint: /logs/admin Response: 400 Error"
                        }
                    ]
            )

            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "Error is querying log insights of AWS CloudWatch")
        else: 
            #parse log events and create DataFrame
            events = []
            for event in response['results']:
                timestamp = datetime.strptime(event[0]['value'], '%Y-%m-%d %H:%M:%S.%f')    #change the timestamp column from millisecond format to datetime
                message = event[1]['value']
                split_msg = message.split(":")  #define strategy to capture endpoint name, user, response code from the log message
                endpoint = split_msg[1].strip().split()[0]  #capture the string for endpoint
                response = split_msg[2].strip().split()[0]   #capture the string for response code
                events.append((timestamp, message, endpoint, response))    #store every detail in events
            
            df_requests = pd.DataFrame(events, columns=['timestamp', 'message', 'endpoint', 'response'])    #create df from events
            clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                    logGroupName = "project-refined-job-postings",
                    logStreamName = "api",
                    logEvents = [
                        {
                        'timestamp' : int(time.time() * 1e3),
                        'message' : "API endpoint: /logs/admin Response: 200 Success"
                        }
                    ]
            )
            return df_requests