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
# from pypdf import PdfReader
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

#authenticate S3 resource with your user credentials that are stored in your .env config file
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

def preprocess_job_descriptions():

    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
            logGroupName = "project-refined-job-postings",
            logStreamName = "airflow",
            logEvents = [
                {
                'timestamp' : int(time.time() * 1e3),
                'message' : "Airflow DAG ID (description-preprocess_v1): Initiated"
                }
            ]
    )

    data_dict = {}  #will store the contents of each file on the S3 bcket as df
    i=0 #being used to check for first object, could also use a boolean flag
    for objects in s3resource.Bucket(user_bucket).objects.filter(Prefix='jobs-scraped/'):   #traverse through the files found on the S3 bucket batch folder
        if(i==0):
            pass    #since the first object is the root directory object, we do not need this so pass
        else:
            if (objects.key == "jobs-scraped/jobs-scraped-historic-for-training/"):
                pass
            else:
                file_name = objects.key #set object key as file name variable
                obj = s3client.get_object(Bucket= user_bucket, Key= file_name) #get object and file (key) from bucket
                df_name = file_name.split('/')[-1].split('.')[0]    #df name excludes the file extension
                data_dict[df_name] = pd.read_csv(obj['Body'])   #save df in a dict
        i+=1    #being used to check for first object, could also use a boolean flag

    #define variables for respective df to enable preprocessing on df
    data_analyst = data_dict['jobs_data_analyst_entry_level']
    data_engg = data_dict['jobs_data_engineer_entry_level']
    data_scientist = data_dict['jobs_data_scientist_entry_level']

    def filter_multiple_new_lines(text):
        pattern = r'\n+'
        text = re.sub(pattern, '\n', text)
        return text

    def filter_emails(text):
        pattern = r'(?:(?!.*?[.]{2})[a-zA-Z0-9](?:[a-zA-Z0-9.+!%-]{1,64}|)|\"[a-zA-Z0-9.+!% -]{1,64}\")@[a-zA-Z0-9][a-zA-Z0-9.-]+(.[a-z]{2,}|.[0-9]{1,})'
        text = re.sub(pattern, '', text)
        return text

    def filter_websites(text):
        pattern = r'(http\:\/\/|https\:\/\/)?([a-z0-9][a-z0-9\-]*\.)+[a-z][a-z\-]*'
        text = re.sub(pattern, '', text)
        return text

    def filter_phone_numbers(text):
        pattern = r'(?:(?:\+|00)33[\s.-]{0,3}(?:\(0\)[\s.-]{0,3})?|0)[1-9](?:(?:[\s.-]?\d{2}){4}|\d{2}(?:[\s.-]?\d{3}){2})|(\d{2}[ ]\d{2}[ ]\d{3}[ ]\d{3})'
        text = re.sub(pattern, '', text)
        return text

    def filter_text(text):
        lines = text.split('\n')
        
        #traverse each word
        for i in range (len(lines)):
            if '401k' in lines[i].split(): 
                lines[i] = '\n' #if word found, replace whole line with \n to eliminate its content
            if 'dental' in lines[i].split(): 
                lines[i] = '\n' #if word found, replace whole line with \n to eliminate its content
            if 'pto' in lines[i].split(): 
                lines[i] = '\n' #if word found, replace whole line with \n to eliminate its content
            if 'eeo' in lines[i].split(): 
                lines[i] = '\n' #if word found, replace whole line with \n to eliminate its content
            if 'more' in lines[i].split():
                lines[i] = '\n' #if word found, replace whole line with \n to eliminate its content
        
        new_text = '\n'.join(lines) #create new text representing cleaned text
        return new_text

    def clean_text(text):
        text = filter_multiple_new_lines(text)
        text = text.lower()
        text = filter_phone_numbers(text)
        text = filter_emails(text)
        text = filter_websites(text)
        text = filter_text(text)
        text = filter_multiple_new_lines(text)
        return text

    #apply the cleaning function to the Description column of each df
    data_analyst['CleanedDescription'] = data_analyst.Description.apply(clean_text)
    data_engg['CleanedDescription'] = data_engg.Description.apply(clean_text)
    data_scientist['CleanedDescription'] = data_scientist.Description.apply(clean_text)

    #trim the df to exclude to old description column
    data_analyst = data_analyst[['Job ID','Title','CleanedDescription']]
    data_engg = data_engg[['Job ID','Title','CleanedDescription']]
    data_scientist = data_scientist[['Job ID','Title','CleanedDescription']]

    #convert df to csv locally
    data_analyst.to_csv('./files/latest_data_analyst_entry_level.csv', index=False)
    data_engg.to_csv('./files/latest_data_engineer_entry_level.csv', index=False)
    data_scientist.to_csv('./files/latest_data_scientist_entry_level.csv', index=False)

    #define S3 path to upload cleaned csv
    key_da = 'dataset/daily/latest_data_analyst_entry_level.csv'
    key_de = 'dataset/daily/latest_data_engineer_entry_level.csv'
    key_ds = 'dataset/daily/latest_data_scientist_entry_level.csv'

    #upload the csv files to S3 bucket
    s3resource.Object(user_bucket, key_da).put(Body=open('./files/latest_data_analyst_entry_level.csv', 'rb'))
    s3resource.Object(user_bucket, key_de).put(Body=open('./files/latest_data_engineer_entry_level.csv', 'rb'))
    s3resource.Object(user_bucket, key_ds).put(Body=open('./files/latest_data_scientist_entry_level.csv', 'rb'))
    
    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
            logGroupName = "project-refined-job-postings",
            logStreamName = "airflow",
            logEvents = [
                {
                'timestamp' : int(time.time() * 1e3),
                'message' : "Airflow DAG ID (description-preprocess_v1): DAG completed"
                }
            ]
    )

    return True

#defining the DAG
with DAG(
    dag_id="description-preprocess_v1",
    schedule="0 0 * * *",   #run daily - at midnight
    start_date=days_ago(0),
    catchup=False,
    tags=["damg7245", "project", "linkedin-scraper", "working"],
) as dag:

    job_descriptions_preprocess = PythonOperator(
        task_id = 'run_jobs_preprocessing',
        python_callable = preprocess_job_descriptions
    )
    
    #the task for this DAG
    job_descriptions_preprocess