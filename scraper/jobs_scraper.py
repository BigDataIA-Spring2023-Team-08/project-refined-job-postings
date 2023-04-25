import os
import logging
import csv
import time
from linkedin_jobs_scraper import LinkedinScraper
from linkedin_jobs_scraper.events import Events, EventData, EventMetrics
from linkedin_jobs_scraper.query import Query, QueryOptions, QueryFilters
from linkedin_jobs_scraper.filters import RelevanceFilters, TimeFilters, TypeFilters, ExperienceLevelFilters, OnSiteOrRemoteFilters
from selenium.common.exceptions import JavascriptException
from pydotenvs import load_env
import boto3

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

#authenticate S3 client for logging with your user credentials that are stored in your .env config file
clientLogs = boto3.client('logs',
                        region_name='us-east-1',
                        aws_access_key_id = aws_log_key,
                        aws_secret_access_key = aws_log_secret
                        )

job_title_idx = 0

#fired once for each successfully processed job
def on_data(data: EventData):

    #upload the necessary data into the df 
    job_data.append([data.job_id, data.title, data.company, data.date, data.link, len(data.description), data.description])

#fired once at end for each processed job
def on_end():

    clientLogs.put_log_events(      #logging to AWS CloudWatch logs
            logGroupName = "project-refined-job-postings",
            logStreamName = "airflow",
            logEvents = [
                {
                'timestamp' : int(time.time() * 1e3),
                'message' : f"Query at index {job_title_idx} completed"
                }
            ]
        )

def on_error(error):
    # if 'javascript error: Cannot read properties of null' in str(error):
    #     pass
    # else:
    #     print('[ON_ERROR]', error)
    pass
    #continue

scraper = LinkedinScraper(
    chrome_executable_path=None,  #custom Chrome executable path (e.g. /foo/bar/bin/chromedriver) 
    chrome_options=None,  #custom Chrome options here
    headless=True,  #overrides headless mode only if chrome_options is None
    max_workers=1,  #how many threads will be spawned to run queries concurrently (one Chrome driver for each thread)
    slow_mo=4,  #slow down the scraper to avoid 'Too many requests 429' errors (in seconds)
    page_load_timeout=40  #page load timeout (in seconds)    
)

#add event listeners
scraper.on(Events.DATA, on_data)
scraper.on(Events.ERROR, on_error)
scraper.on(Events.END, on_end)

#define the queries to run using scraper in a list
queries = [
    Query(
        query='Data Analyst',   #query for data analyst jobs
        options=QueryOptions(
            locations=['United States'],
            apply_link=True,
            skip_promoted_jobs=True,  #skip promoted jobs
            limit=25,
            filters=QueryFilters(
                  time=TimeFilters.DAY, #posted in the last day
                  type=[TypeFilters.FULL_TIME],
                  experience=[ExperienceLevelFilters.ENTRY_LEVEL]
            )
        )
    ),
    # Query(
    #     query='Data Analyst',
    #     options=QueryOptions(
    #         locations=['United States'],
    #         apply_link=True,  # Try to extract apply link (easy applies are skipped). If set to True, scraping is slower because an additional page mus be navigated. Default to False.
    #         skip_promoted_jobs=True,  # Skip promoted jobs. Default to False.
    #         limit=25,
    #         filters=QueryFilters(
    #               time=TimeFilters.DAY,
    #               type=[TypeFilters.FULL_TIME],
    #               experience=[ExperienceLevelFilters.ASSOCIATE]
    #         )
    #     )
    # ),
    Query(
        query='Data Scientist', #query for data scientist jobs
        options=QueryOptions(
            locations=['United States'],
            apply_link=True, 
            skip_promoted_jobs=True,  #skip promoted jobs
            limit=25,
            filters=QueryFilters(
                  time=TimeFilters.DAY, #posted in the last day
                  type=[TypeFilters.FULL_TIME],
                  experience=[ExperienceLevelFilters.ENTRY_LEVEL]
            )
        )
    ),
    # Query(
    #     query='Data Scientist',
    #     options=QueryOptions(
    #         locations=['United States'],
    #         apply_link=True,  # Try to extract apply link (easy applies are skipped). If set to True, scraping is slower because an additional page mus be navigated. Default to False.
    #         skip_promoted_jobs=True,  # Skip promoted jobs. Default to False.
    #         limit=25,
    #         filters=QueryFilters(
    #               time=TimeFilters.DAY,
    #               type=[TypeFilters.FULL_TIME],
    #               experience=[ExperienceLevelFilters.ASSOCIATE]
    #         )
    #     )
    # ),
    Query(
        query='Data Engineer',  #query for data engineer jobs
        options=QueryOptions(
            locations=['United States'],
            apply_link=True,
            skip_promoted_jobs=True,  #skip promoted jobs
            limit=25,
            filters=QueryFilters(
                  time=TimeFilters.DAY, #posted in the last day
                  type=[TypeFilters.FULL_TIME],
                  experience=[ExperienceLevelFilters.ENTRY_LEVEL]
            )
        )
    ),
    # Query(
    #     query='Data Engineer',
    #     options=QueryOptions(
    #         locations=['United States'],
    #         apply_link=True,  # Try to extract apply link (easy applies are skipped). If set to True, scraping is slower because an additional page mus be navigated. Default to False.
    #         skip_promoted_jobs=True,  # Skip promoted jobs. Default to False.
    #         limit=25,
    #         filters=QueryFilters(
    #               time=TimeFilters.DAY,
    #               type=[TypeFilters.FULL_TIME],
    #               experience=[ExperienceLevelFilters.ASSOCIATE]
    #         )
    #     )
    # )
]

job_titles_searched = ['data_analyst_entry_level', 'data_scientist_entry_level', 'data_engineer_entry_level']   #list for filenames

clientLogs.put_log_events(      #logging to AWS CloudWatch logs
            logGroupName = "project-refined-job-postings",
            logStreamName = "airflow",
            logEvents = [
                {
                'timestamp' : int(time.time() * 1e3),
                'message' : "LinkedIn job scraper script initiated"
                }
            ]
        )

for q in queries:   #for each query inside the query list
    job_data = []   #create a list to store the scraped job data
    scraper.run(q)  #run the scraper
    
    #save job data to a CSV file
    with open(f'jobs_scraped/jobs_{job_titles_searched[job_title_idx]}.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Job ID', 'Title', 'Company', 'Date', 'Link', 'Description Length','Description'])
        writer.writerows(job_data)
    
    processed_file = f'jobs_scraped/jobs_{job_titles_searched[job_title_idx]}.csv'  #define local path
    s3_file_path = 'jobs-scraped/' + f'jobs_{job_titles_searched[job_title_idx]}.csv'  #defined path for S3 folder
    s3resource.meta.client.upload_file(processed_file, user_bucket, s3_file_path)   #upload the scraped data as a csv to S3 bucket
    job_title_idx+=1

clientLogs.put_log_events(      #logging to AWS CloudWatch logs
            logGroupName = "project-refined-job-postings",
            logStreamName = "airflow",
            logEvents = [
                {
                'timestamp' : int(time.time() * 1e3),
                'message' : "LinkedIn job scraper completed successfully"
                }
            ]
        )