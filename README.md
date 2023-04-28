# CareerCompass: Refined Job Postings Finder - FINAL PROJECT

![Profile data-cuate](https://user-images.githubusercontent.com/46862684/235030798-104e366f-8cd0-4c35-9c84-3d6f812eda89.svg)

##### Image Source: [Storyset](https://storyset.com/)
----- 

> ✅ Active status <br>
> [🚀 Application link](http://34.74.232.103:8003/) <br>
> [⏱ Airflow](http://34.74.232.103:8082/) <br>
> [🧑🏻‍💻 FastAPI](http://34.74.232.103:8002/docs) <br>
> [🎬 Codelab Slides](https://codelabs-preview.appspot.com/?file_id=1p63_TG8gJMdh3_X-U4dJAxjosIJW98NqSb7plLFZ_bI#0) <br>
>  🐳 Docker Hub Images: [FastAPI](https://hub.docker.com/repository/docker/mashruwalav/job-finder-api_v2/general), [Streamlit](https://hub.docker.com/repository/docker/mashruwalav/job-finder-app_v2/general) <br>
> [📽️ Application Demo/Usage]()

----- 

## Index
  - [Problem Statement 🤔](#problem-statement)
  - [Objective 🎯](#objective)
  - [Abstract 📝](#abstract)
  - [Architecture Diagram 🏗](#architecture-diagram)
  - [Model Selection & Comparisons 🧬](#model-selection-and-comparisons)
  - [Project Components 💽](#project-components)
    - [Scraping Jobs](#scraping-jobs)
    - [FastAPI](#fastapi)
    - [Streamlit](#streamlit)
    - [Airflow](#airflow)
    - [Great Expectations](#great-expectations)
    - [AWS CloudWatch](#aws-cloudwatch)
  - [How to run the application 💻](#how-to-run-the-application-locally)
----- 

## Problem Statement
In this tough employment market where job seekers are incessantly applying for various job roles everyday, much of their time and energy is exhausted in reading job descriptions and searching for job postings that best matches their profile. 

Through our proposed application, we aim to mitigate the stress and provide a solution to address the problem by helping job applicants get matched to job roles and positions they could potentially be a great fit for!

## Objective
Building an application to assist job seekers in saving time by providing personalised job recommendations based on their resume. The application aims to simplify the job search process by using Count Vectorizer to match the job seeker's skills and experience with the most relevant job postings. By presenting the top 3 matched job postings daily, the application helps job seekers to focus on the most promising opportunities, increasing their chances of success and ultimately saving their time and effort in the job search process. 

## Abstract
The task involves building a decoupled architecture for the application:
- Get job postings most relevant to your resume with the help of this application

- Upload your resume and provide the role you are looking for (Data Scientist, Data Analyst, Data Engineer) and generate vector representations from your resume to be matched against Job Descriptions

- Scrape Job Postings from LinkedIn by using web scraping python package linkedin-scraper

- Calculate Cosine Similarity score on vectors generated by using TF-IDF on resume and job descriptions. Display top 3 jobs by highest cosine similarity value for the recommendation

- Access the application through Streamlit which pulls a Docker image of the application

- Backend processes are handled through Airflow which again uses a Docker image of the Airflow instance



## Architecture Diagram
![arch-diag](https://github.com/BigDataIA-Spring2023-Team-08/assignment05-fit-finder-app/blob/main/application-use-test-cases/ff-motion.png)

## Model Selection and Comparisons

In order to properly engineer our application & use case we had to explore the options available for us. We initially decided to fine-tune BERT and use it. However, we ran into multiple issues. We have also tried other models and did comparisons before selecting our final model. All necessary details (test code, findings, comments, models compared) can be found in this document which we have maintained: [Findings for ML models or Model as a Service](https://docs.google.com/document/d/1gTjyj82cb5uPjKOrgoDWziR6oFk9DpJVQcfjh2GHEJ4/edit?usp=sharing)

## Project Components

### Scraping Jobs
LinkedIn jobs are scraped for the three job titles considered in our application, namely, Data Analyst, Data Engineer, Data Scientist 

We will like to thank the user/group for developing this LinkedIn scraper which is available, we use this code and edit things as per our use case to perform the job scraping: [LinkedIn job scraper](https://pypi.org/project/linkedin-jobs-scraper/)

### FastAPI
[FastAPI](https://fastapi.tiangolo.com/) is a modern, high-performance web framework used for building RESTful APIs in Python which enables developers to implement the REST interface to call commonly used functions for use in applications. In this application, the framework has been implemented to create endpoints to interact with various services.

### Streamlit
Python library [Streamlit](https://streamlit.iohttps://streamlit.io) has been implemented in this application for its user interface. Streamlit offers user friendly experience to assist users in :

1) Enabling users to create an account and upload their resumes
2) Display details of refined jobs that best matches the user's profile along with job link for users to apply immediately

Streamlit UI flow: 
1) User has option to Login, Signup & Change Password 
    - If the forgot password page is selected, user can update their password. The new password has to be more than 4 characters
    - Else, user can sign up using our sign up form
    - Finally, user can login to the application to view their account
2) Once a user logins for the first time, the user is asked to upload their resume (only .docx format allowed)
    - To achieve the preprocessing, an airflow DAG run is triggered to performs the processing on the resume jut uploaded 
3) After uploading their resume, user can select one of the 3 listed job titles and hit the Get Job Recommendations button to get 3 best job listings based on their resume: 
    - To achieve this, in the background 2 processes are initiated. The first is an airflow DAG run trigger to prepare dataset based on user’s resume & the job title selected and the 2nd is a FastAPI call to the model endpoint which takes as input the output that is generated by the DAG run just mentioned previously


### Airflow
Airflow is an open-source platform for data orchestration, through which data workflows can be scheduled, monitored and managed. In this application, Airflow is integrated to automate and schedule the workflow of the application with the help of DAGs to retrieve data from job boards (LinkedIn) every 24 hours as well as perform data quality checks.

Airflow consists of 3 DAGs. 2 of these DAGs are triggered through a RESTAPI call to the Airflow instance via a click on the Streamlit UI. The 3rd DAG is automated and runs every midnight. 

1) Let us first look at the last mentioned DAG above which runs at midnight. This DAG [`prepare_descriptions_dag.py`](https://github.com/BigDataIA-Spring2023-Team-08/project-refined-job-postings/blob/main/airflow/dags/prepare_descriptions_dag.py) fetches the scraped jobs csv from the S3 bucket (which has already been validated using GreatExpectation). After this, each job description is cleaned to remove emails, phone numbers & (more importantly) sentences which mention about ‘401k’, ‘insurance’, ‘EEO’, ‘equal employer opportunity’ - since all of these are irrelevant text for us to perform similarity calculations
2) The other DAG is the one which runs when a user uploads their resume on streamlit. This DAG [`prepare_resumes_dag.py`](https://github.com/BigDataIA-Spring2023-Team-08/project-refined-job-postings/blob/main/airflow/dags/prepare_resumes_dag.py) is triggered through a RESTAPI call and it saves the resume file to S3 bucket as well as preprocess the resume text to remove emails, phone numbers, years & months mentioned
3) The final DAG is the one which creates a dataset that will be sent to the Model. This DAG [`prepare_dataset_dag.py`](https://github.com/BigDataIA-Spring2023-Team-08/project-refined-job-postings/blob/main/airflow/dags/prepare_dataset_dag.py) is triggered when the user clicks the get job recommendation button on the streamlit UI. This DAG takes the user’s cleaned resume (which was uploaded by the DAG mentioned in point 2) & the select job title’s clean job descriptions (which was uploaded by the DAG mentioned in point 1). A dataset is created which will be given to the model to find predictions

### Great Expectations
[Great Expectations](https://docs.greatexpectations.io/docs/) is a tool used to validate, document and profile data in order to eliminate pipeline debt.
- The python library has been used with Amazon Web Services (AWS) using S3 to validate,document and generate reports for jobs data scraped from LinkedIn and stored in S3 bucket.
- The data quality checks have been automated and scheduled every midnight using Apache Airflow orchestration tool with the use of 3 DAG's (Directed Acyclic Graphs)
1) **download_csv_files DAG** -

> `Task`: ***download_csv_files DAG*** downloads the csv data files of jobs scraped from LinkedIn and stored in S3 buckets into a data folder which is being used as a `Datasource` inside the Great Expectations directory.

2) **validate_s3_data DAG** -

> `Task`: ***validate_s3_data DAG*** validates, documents and generates reports of the downloaded csv data files. It creates data context, data source, data connectors, and data asset objects which are then being used to create expectation suites using validators and finally create,run and save the checkpoints for each csv file. This results in the creation of an html report of the csv data.

3) **publish_s3_jobs_data_report DAG** -

> `Task`: ***publish_s3_jobs_data_report DAG*** uploads the html validation reports executed by the previous dag to a result folder of the S3 bucket which can then be viewed through static web hosting.

### AWS CloudWatch
Logging is an essential part of any code/application. It gives us details about code functioning and can be helpful while testing out the code. Not only this, logging user level actions also gives an idea about what actions are being performed both in the UI as well as the functions being executed in our backend. We implement logs using AWS CloudWatch.

Set up for logging to AWS CloudWatch:
For this, you need to set up an IAM AWS user with a policy attached for full access to logs. After this, generate your credentials as previously done for the boto3 client and store these logging credentials in the .env configuration file as AWS_LOG_ACCESS_KEY and AWS_LOG_SECRET_KEY.

After this, we create a log group within CloudWatch and 3 different log streams as follows:
  - <b>api:</b> to store logs of all activity related to the FastAPI endpoints calls, response code & messages
  - <b>airflow:</b> logs for Airflow DAGs run
  - <b>ui:</b> logs the pages user opens while running our application, or when any error response is encountered. Also notes when a DAG is triggered or API endpoint is called

## How to run the application locally

1. Clone the repo to get all the source code on your machine
2. Within the airflow folder, create a .env file with just the following line: 
  ```
  AIRFLOW_UID=1001
  ```
3. Note: no need to add your credentials in this .env file since the credentials for the airflow app are to be added as said in the next point
4. Edit lines 66-70 in the [`docker-compose.yml`](https://github.com/BigDataIA-Spring2023-Team-08/project-refined-job-postings/blob/main/airflow/docker-compose.yaml) found within the airflow folder to add your API keys
5. Finally, execute following line to get airflow running: 
  ```
  docker compose up -d
  ```
6. Lets us get the CareerCompass app running now:
7. There is a docker-compose file in the main directory, this is used to get the application running. Within the [`docker-compose.yml`](https://github.com/BigDataIA-Spring2023-Team-08/project-refined-job-postings/blob/main/docker-compose.yml) file, edit lines 14-18 and 30-37 with your credentials
8. Finally, execute following line to get it running: 
  ```
  docker compose up -d
  ```

-----
> WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK.
> 
> Vraj: 25%, Poojitha: 25%, Merwin: 25%, Anushka: 25%
-----
