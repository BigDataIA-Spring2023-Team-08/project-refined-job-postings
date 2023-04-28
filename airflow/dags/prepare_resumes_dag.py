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

def preprocess_resume_descriptions(**kwargs):
    """DAG's function to preprocess a user's resume by reading the text and cleaning it and then storing it as a csv
    of 25 rows in S3. Resume of the user is selected using the input parameters provided which help fetch 
    the user's resume content.
    -----
    Input parameters:
    Dynamic input parameters defined using kwargs. However, for our use-case on every trigger of this DAG, we provide
    the conf vairable with the key and value pairs. We provide:
    username : string
        the username of the user who triggered the DAG run from streamlit UI
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
                'message' : "Airflow DAG ID (resume-preprocess_v1): Initiated"
                }
            ]
    )

    username = kwargs['dag_run'].conf.get('username')   #get the username which is provided as an argument in the restapi call
    resume_df = pd.DataFrame(columns=['ResumeName','ResumeText'])   #df for storing the data: consists of 2 columns
    
    i=0 #being used to check for first object, could also use a boolean flag
    for objects in s3resource.Bucket(user_bucket).objects.filter(Prefix='dataset/user-uploads/'):   #traverse through the files on the S3 bucket consisting user uploads
        if(i==0):
            pass    #since the first object is the root directory object, we do not need this so pass
        else:
            file_path = objects.key #set object key as file name variable
            obj = s3client.get_object(Bucket= user_bucket, Key= file_path) #get object and file (key) from S3
            file_name = file_path.split('/')[-1]    #file name excludes the file extension
           
            text = ""   #to read contents of the resume and store as a single string
            if file_name == f'resume_{username}.docx':
                s3client.download_file(user_bucket, file_path, f'./files/{file_name}')  #download the file to local folder
                doc = docx.Document(f'./files/{file_name}')
                fulltext = []
                for para in doc.paragraphs: #read contents
                    fulltext.append(para.text)
                text = '\n'.join(fulltext)  #store in text
                resume_df.loc[len(resume_df.index)] = [file_name, text] #append a single row in df for each resume
                break

        i+=1    #being used to check for first object, could also use a boolean flag

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
        pattern = r'(\d{3}[-.\s]?\d{4}|\(\d{3}\)\s?\d{3}[-.\s]?\d{4}|\+\d{1,2}\s?\d{3}[-.\s]?\d{3}[-.\s]?\d{4})'
        text = re.sub(pattern, '', text)
        return text
    
    def filter_chars(text):
        pattern = r'[?$|!-()<>]'
        text = re.sub(pattern, '', text)
        return text

    def filter_year(text):
        pattern = r'[1-3][0-9]{3}'
        text = re.sub(pattern, '', text)
        return text

    def filter_text(text):
        lines = text.split('\n')
    
        for i in range (len(lines)):    #traverse through each line
            lines[i] = lines[i].strip()

            #find if a month is mentioned
            if ('jan' in lines[i].split() or 'feb' in lines[i].split() or 'mar' in lines[i].split() or 'apr' in lines[i].split() 
            or 'may' in lines[i].split() or 'jun' in lines[i].split() or 'jul' in lines[i].split() or 'aug' in lines[i].split() or 'sep' in lines[i].split() 
            or 'oct' in lines[i].split() or 'nov' in lines[i].split() or 'dec' in lines[i].split()): 
                lines[i] = '\n' #replace whole line with \n to eliminate its content

            #find if a month is mentioned
            if ('january' in lines[i].split() or 'february' in lines[i].split() or 'march' in lines[i].split() or 'april' in lines[i].split() 
            or 'may' in lines[i].split() or 'june' in lines[i].split() or 'july' in lines[i].split() or 'august' in lines[i].split() or 'september' in lines[i].split() 
            or 'october' in lines[i].split() or 'november' in lines[i].split() or 'december' in lines[i].split()): 
                lines[i] = '\n' #replace whole line with \n to eliminate its content

        new_text = '\n'.join(lines) #create new text representing cleaned text
        return new_text

    def clean_text(text):
        """
        This fucntion cleans the given chunks of text by removing extra spaces, converting to lower case, removing email,
        phone numbers, websites, years, certain special characters & months mentioned in a resume
        -----
        Input parameters:
            text: string of text from resume
        -----
        Returns:
            text: cleaned text

        """
        text = text.replace("\t", "\n") #replace tab spaces with a line break
        text = filter_multiple_new_lines(text)  
        text = text.lower() #convert text to lower case
        text = text.strip() #strip whitespaces
        text = filter_phone_numbers(text)
        text = filter_emails(text)
        text = filter_websites(text)
        text = filter_chars(text)
        text = filter_year(text)
        text = filter_text(text)
        text = filter_multiple_new_lines(text)
        return text #return cleaned text

    resume_df['CleanedText'] = resume_df.ResumeText.apply(clean_text)   #apply the cleaning function to the ResumeText column
    resume_df = resume_df[['ResumeName','CleanedText']] #trim the df to exclude the old description column
    resume_df = resume_df.append([resume_df]*24,ignore_index=True)  #replicate the row 24 times to get total of 25 rows since there will be 25 job descriptions to compare against each time
    resume_df.to_csv(f'./files/res_{username}.csv', index=False)    #convert df to csv locally
    key = f'dataset/user-uploads/res_{username}.csv'    #define S3 path to upload cleaned csv
    s3resource.Object(user_bucket, key).put(Body=open(f'./files/res_{username}.csv', 'rb')) #upload csv to S3

    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
            logGroupName = "project-refined-job-postings",
            logStreamName = "airflow",
            logEvents = [
                {
                'timestamp' : int(time.time() * 1e3),
                'message' : "Airflow DAG ID (resume-preprocess_v1): DAG completed"
                }
            ]
    )

    return True

#defining the DAG
with DAG(
    dag_id="resume-preprocess_v1",
    #schedule="0 0 * * *",   #run daily - at midnight
    start_date=days_ago(0),
    catchup=False,
    tags=["damg7245", "project", "processing", "working"],
) as dag:

    resume_descriptions_preprocess = PythonOperator(
        task_id = 'run_resumes_preprocessing',
        python_callable = preprocess_resume_descriptions
    )
    
    #the task for this DAG
    resume_descriptions_preprocess