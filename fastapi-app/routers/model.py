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
    prefix="/model",
    tags = ['Model']
)

get_db = userdb.get_db

@router.get('/relevantjobs', status_code=status.HTTP_200_OK)
async def get_relevant_jobs(username: str, jobtitle: str, current_user: schema.User = Depends(oauth2.get_current_user)):
    """ Function to get the relevant jobs for a particular user. This is the model we offer to the user as a service. 
    The model finds the top 3 best matched jobs to the user based of their resume & the job title selected.
    Input parameters:
    username : str
        The username of the user whose resume file name will be used.
    jobtitle : str
        Selected job title from the UI
    -----
    Returns:
    top3_list : list
        A list consisting links to the best 3 jobs for the user.
    """

    #authenticate S3 client for logging with your user credentials that are stored in your .env config file
    clientLogs = boto3.client('logs',
                            region_name='us-east-1',
                            aws_access_key_id = os.environ.get('AWS_LOG_ACCESS_KEY'),
                            aws_secret_access_key = os.environ.get('AWS_LOG_SECRET_KEY')
                            )

    #authenticate S3 resource with your user credentials that are stored in your .env config file
    s3resource = boto3.resource('s3',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )

    #authenticate S3 client with your user credentials that are stored in your .env config file
    s3client = boto3.client('s3',
                        region_name='us-east-1',
                        aws_access_key_id = os.environ.get('AWS_ACCESS_KEY'),
                        aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
                        )

    #get user bucker name
    user_bucket = os.environ.get('USER_BUCKET_NAME')
    jobtitle = jobtitle.replace(" ", "_").lower()

    for objects in s3resource.Bucket(user_bucket).objects.filter(Prefix='dataset/adhoc/'):   #traverse through the files found on the S3 bucket batch folder
            file_name = objects.key #set object key as file name variable
            obj = s3client.get_object(Bucket= user_bucket, Key= file_name) #get object and file (key) from bucket
            dataset_name = file_name.split('/')[-1].split('.')[0]    #dataset name excludes the file extension
            if dataset_name == f'dataset_{username}':   #find adhoc dag of the selection
                df_main = pd.read_csv(obj['Body'])   #save as df
                break

    # Create a new TfidfVectorizer object and fit it on concatenated list of job descriptions and resumes
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    jd_and_resumes = df_main['CleanedDescription'].tolist() + df_main['CleanedText'].tolist()
    tfidf_vectorizer.fit(jd_and_resumes)    #fit the tfidf model

    # Transform the job descriptions and resumes using the vectorizer
    jd_tfidf = tfidf_vectorizer.transform(df_main['CleanedDescription'])
    resume_tfidf = tfidf_vectorizer.transform(df_main['CleanedText'])

    # Compute the cosine similarity between each job description and its corresponding resume
    df_main['cosine_sim'] = [cosine_similarity(jd_tfidf[i], resume_tfidf[i])[0][0] for i in range(len(df_main))]
    
    #sort similarities in descending order, and store the job id for top 3 jobs
    out_df = df_main.sort_values('cosine_sim', ascending=False)
    job_ids = out_df["Job ID"]
    top_jobs = job_ids.head(3)
    
    #now we need to find the job link for these top 3 jobs, this link is available in the scraped job descriptions data file
    for objects in s3resource.Bucket(user_bucket).objects.filter(Prefix='jobs-scraped/'):   #traverse through the files found on the S3 bucket batch folder
        file_name = objects.key #set object key as file name variable
        obj = s3client.get_object(Bucket= user_bucket, Key= file_name) #get object and file (key) from bucket
        if file_name == f'jobs-scraped/jobs_{jobtitle}_entry_level.csv': #find the csv file of the selected job title
            jt_df = pd.read_csv(obj['Body'])   #save as df
            break

    top3_df = jt_df.loc[jt_df['Job ID'].isin(top_jobs)] #find the index for the job id obtained previously in top_jobs
    top3_dict = {}
    
    if top3_df.empty:
        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /model/relevantjobs Response: 404 User resume not uploaded"
                    }
                ]
        )

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "Top 3 jobs not found!")
    else:

        top3_dict['link'] = top3_df['Link'].tolist()    #convert to a list, this contains 3 links
        top3_dict['company'] = top3_df['Company'].tolist()

        clientLogs.put_log_events(      #logging to AWS CloudWatch logs
                logGroupName = "project-refined-job-postings",
                logStreamName = "api",
                logEvents = [
                    {
                    'timestamp' : int(time.time() * 1e3),
                    'message' : "API endpoint: /model/relevantjobs Response: 200 Success"
                    }
                ]
        )
        return top3_dict