# CareerCompass: Refined Job Postings Finder - FINAL PROJECT

![Profile data-cuate](https://user-images.githubusercontent.com/46862684/235030798-104e366f-8cd0-4c35-9c84-3d6f812eda89.svg)

##### Image Source: [Storyset](https://storyset.com/)
----- 

> ✅ Active status <br>
> [🚀 Application link](http://34.73.90.193:8082) <br>
> [⏱ Airflow](http://34.73.90.193:8081) <br>
> [🎬 Codelab Slides](https://codelabs-preview.appspot.com/?file_id=1p63_TG8gJMdh3_X-U4dJAxjosIJW98NqSb7plLFZ_bI#0) <br>
>  🐳 Docker Hub Images: [Airflow](https://hub.docker.com/repository/docker/mashruwalav/echonotes_airflow_v2/general), [Streamlit](https://hub.docker.com/repository/docker/mashruwalav/echonotes_streamlitapp_v2/general) <br>
> [📽️ Application Demo/Usage](https://drive.google.com/file/d/1JTiC1osBSS4qvRr9irH4fNb4Yrf8YlXz/view?usp=sharing)

----- 

## Index
  - [Problem Statement 🤔](#problem-statement)
  - [Objective 🎯](#objective)
  - [Abstract 📝](#abstract)
  - [Architecture Diagram 🏗](#architecture-diagram)
  - [Repository Components 🗃️](#repository-components)
  - [Project Components 💽](#project-components)
    - [FastAPI](#fastapi)
    - [Streamlit](#streamlit)
    - [Airflow](#airflow)
    - [Great Expectations](#great-expectations)
  - [Application Use Cases 📸](#application-use-cases)
  - [How to run the application 💻](#how-to-run-the-application-locally)
----- 

## Problem Statement
In this tough employment market where job seekers are incessantly applying for various job roles everyday, much of their time and energy is exhausted in reading job descriptions and searching for job postings that best matches their profile. 

Through our proposed application, we aim to mitigate the stress and provide a solution to address the problem by helping job applicants get matched to job roles and positions they could potentially be a great fit for!

## Objective
To build an application that provides users and job applicants with refined job postings daily based on their resume. As a function of this service, users will be recommended 3 job descriptions that best matches the experience and skillsets present on their resume.

## Abstract

Tasks involved to build the application are as follows:


## Architecture Diagram

## Repository Components

## Project Components

### FastAPI
[FastAPI](https://fastapi.tiangolo.com/) is a modern, high-performance web framework used for building RESTful APIs in Python which enables developers to implement the REST interface to call commonly used functions for use in applications. In this application, the framework has been implemented to create endpoints to interact with various services.

### Streamlit
Python library [Streamlit](https://streamlit.iohttps://streamlit.io) has been implemented in this application for its user interface. Streamlit offers user friendly experience to assist users in :

1) Enabling users to create an account and upload their resumes
2) Display details of refined jobs that best matches the user's profile along with job link for users to apply immediately


### Airflow
Airflow is an open-source platform for data orchestration, through which data workflows can be scheduled, monitored and managed. In this application, Airflow is integrated to automate and schedule the workflow of the application with the help of DAGs to retrieve data from job boards (LinkedIn) every 24 hours as well as perform data quality checks.

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

## How to run the application locally

-----
> WE ATTEST THAT WE HAVEN’T USED ANY OTHER STUDENTS’ WORK IN OUR ASSIGNMENT AND ABIDE BY THE POLICIES LISTED IN THE STUDENT HANDBOOK.
> 
> Vraj: 25%, Poojitha: 25%, Merwin: 25%, Anushka: 25%
-----
