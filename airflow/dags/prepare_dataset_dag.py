from airflow.models import DAG
from airflow.operators.bash_operator import BashOperator
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from airflow.models.param import Param
import os
import pandas as pd
from pydotenvs import load_env
import boto3
import time
import re
import json
import docx

#load local environment
load_env()

#define global variables
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY')
aws_secret_access_key = os.environ.get('AWS_SECRET_KEY')
aws_log_key = os.environ.get('AWS_LOG_ACCESS_KEY')
aws_log_secret = os.environ.get('AWS_LOG_SECRET_KEY')
user_bucket = os.environ.get('USER_BUCKET_NAME')

#authenticate S3 resource with your user credentials that are stored in your .env config file
s3resource = boto3.resource('s3',
                    region_name='us-east-1',
                    aws_access_key_id = aws_access_key_id,
                    aws_secret_access_key = aws_secret_access_key
                    )

#authenticate S3 client with your user credentials that are stored in your .env config file
s3client = boto3.client('s3',
                    region_name='us-east-1',
                    aws_access_key_id = aws_access_key_id,
                    aws_secret_access_key = aws_secret_access_key
                    )

#authenticate S3 client for logging with your user credentials that are stored in your .env config file
clientLogs = boto3.client('logs',
                        region_name='us-east-1',
                        aws_access_key_id = aws_log_key,
                        aws_secret_access_key = aws_log_secret
                        )

def prepare_dataset(**kwargs):
    """DAG's function to prepare adhoc dataset containing job descriptions & resume content as a csv. The csv
    is uploaded to the S3 bucket. Dataset is created using the input parameters provided which help fetch 
    the user's resume content and the job descriptions for the job title selected.
    -----
    Input parameters:
    Dynamic input parameters defined using kwargs. However, for our use-case on every trigger of this DAG, we provide
    the conf vairable with the key and value pairs. We provide:
    username : string
        the username of the user who triggered the DAG run from streamlit UI
    job_title: string
        the job title selected by user from the streamlit UI
    -----
    Returns:
    True
    """

    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
            logGroupName = "project-refined-job-postings",
            logStreamName = "airflow",
            logEvents = [
                {
                'timestamp' : int(time.time() * 1e3),
                'message' : "Airflow DAG ID (prepare-dataset-for-user_v1): Initiated"
                }
            ]
    )

    ########### provide username & selected job title from streamlit
    username = kwargs['dag_run'].conf.get('username')
    job_title = kwargs['dag_run'].conf.get('job_title')
    job_title = job_title.replace(" ", "_").lower()
 
    jobs_df = pd.DataFrame()  #will store the contents of each file on the S3 bcket as df
    resume_df = pd.DataFrame()

    for objects in s3resource.Bucket(user_bucket).objects.filter(Prefix='dataset/daily/'):   #traverse through the files found on the S3 bucket batch folder
        file_name = objects.key #set object key as file name variable
        obj = s3client.get_object(Bucket= user_bucket, Key= file_name) #get object and file (key) from bucket
        df_name = file_name.split('/')[-1].split('.')[0]    #df name excludes the file extension
        if df_name == f"latest_{job_title}_entry_level":
            jobs_df = pd.read_csv(obj['Body'])   #save as df
            break
    
    for objects in s3resource.Bucket(user_bucket).objects.filter(Prefix='dataset/user-uploads/'):   #traverse through the files found on the S3 bucket batch folder
        file_path = objects.key #set object key as file name variable
        obj = s3client.get_object(Bucket= user_bucket, Key= file_path) #get object and file (key) from S3
        file_name = file_path.split('/')[-1]    #file name excludes the file extension
        if file_name == f'res_{username}.csv':
            resume_df = pd.read_csv(obj['Body'])   #save as df
            break

    jobs_df = jobs_df[['Job ID', 'CleanedDescription']]
    
    #constructing the training df with the relevant data
    model_df = pd.concat([jobs_df, resume_df], axis = 1)    
    model_df.to_csv(f'./files/dataset_{username}.csv', index=False)    #convert df to csv locally
    key = f'dataset/adhoc/dataset_{username}.csv'    #define S3 path to upload training csv
    s3resource.Object(user_bucket, key).put(Body=open(f'./files/dataset_{username}.csv', 'rb')) #upload csv to S3

    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
            logGroupName = "project-refined-job-postings",
            logStreamName = "airflow",
            logEvents = [
                {
                'timestamp' : int(time.time() * 1e3),
                'message' : "Airflow DAG ID (prepare-dataset-for-user_v1): DAG completed"
                }
            ]
    )

    return True

#defining the DAG
with DAG(
    dag_id="prepare-dataset-for-user_v1",
    #schedule="0 0 * * *",   #run daily - at midnight
    start_date=days_ago(0),
    catchup=False,
    tags=["damg7245", "project", "prepare-dataset", "working"],
) as dag:

    make_dataset = PythonOperator(
        task_id = 'run_dataset_preparation',
        python_callable = prepare_dataset
    )
    
    #the task for this DAG
    make_dataset