from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from dotenv import load_dotenv
import boto3
import great_expectations as ge
from great_expectations.data_context import DataContext
import os
import re
import json
from airflow.utils.dates import days_ago


# load env variables
load_dotenv()

# AWS CSVs PATH
FOLDER_PATH = 'jobs-scraped/'

# AWS Report Path
REPORT_PATH = 'data-validation-reports-GE/index.html'

# AIRFLOW PATH
# absolute_path = os.path.dirname(__file__)
# relative_path = "working_data/"
# local_path = os.path.join(absolute_path[:-5], relative_path)
base_path = "/opt/airflow/working_dir"

ge_directory_full_path = os.path.join(base_path, "great_expectations")
ge_data_full_path = os.path.join(base_path, "great_expectations/data/")
ge_expectations_full_path = os.path.join(
    base_path, "great_expectations/expectations/")
ge_checkpoints_full_path = os.path.join(
    base_path, "great_expectations/checkpoints/")
ge_datadocs_full_path = os.path.join(
    base_path, "great_expectations/uncommitted/data_docs/local_site/")

# GreatExpectations path

# ge_directory_relative_path = 'working_dir/great_expectations/'
# ge_data_relative_path = 'working_dir/great_expectations/data/'
# ge_expectations_relative_path = 'working_dir/great_expectations/expectations/'
# ge_checkpoints_relative_path = 'working_dir/great_expectations/checkpoints/'
# ge_datadocs_relative_path = 'working_dir/great_expectations/uncommitted/data_docs/local_site/'

# ge_data_full_path = os.path.join(absolute_path[:-5], ge_data_relative_path)

# ge_directory_full_path = os.path.join(
#     absolute_path[:-5], ge_directory_relative_path)

# ge_expectations_full_path = os.path.join(
#     absolute_path[:-5], ge_expectations_relative_path)

# ge_checkpoints_full_path = os.path.join(
#     absolute_path[:-5], ge_checkpoints_relative_path)

# ge_datadocs_full_path = os.path.join(
#     absolute_path[:-5], ge_datadocs_relative_path)

# ge_directory_full_path = '/opt/airflow/working_dir/great_expectations/'
# ge_data_full_path = '/opt/airflow/working_dir/great_expectations/data/'
# ge_expectations_full_path = '/opt/airflow/working_dir/great_expectations/expectations/'
# ge_checkpoints_full_path = '/opt/airflow/working_dir/great_expectations/checkpoints/'
# ge_datadocs_full_path = '/opt/airflow/working_dir/great_expectations/uncommitted/data_docs/local_site/'


# Environment Variables
ENV_BUCKET = os.environ.get(
    'USER_BUCKET_NAME')

ENV_AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')

ENV_AWS_SECRET_KEY = os.environ.get('AWS_SECRET_KEY')

# S3 connection
s3 = boto3.client('s3', aws_access_key_id=ENV_AWS_ACCESS_KEY,
                  aws_secret_access_key=ENV_AWS_SECRET_KEY)

response = s3.list_objects_v2(Bucket=ENV_BUCKET, Prefix=FOLDER_PATH)

# Storing path to CSVs using list Comprehension
csv_files_path = [obj["Key"]
                  for obj in response["Contents"] if obj["Key"].endswith(".csv")]


# define a PythonOperator to download the CSV files
def download_csv_files():

    # get a list of the CSV files in the S3 bucket
    response = s3.list_objects_v2(Bucket=ENV_BUCKET, Prefix=FOLDER_PATH)
    csv_files_path = [obj["Key"]
                      for obj in response["Contents"] if obj["Key"].endswith(".csv")]

    # download each CSV file to the local filesystem
    # for csv_file_path in csv_files_path:
    #     s3.download_file(
    #         ENV_BUCKET, csv_file_path, local_path+csv_file_path)

    # download each CSV file to the GreatExpectations folder
    for csv_file_path in csv_files_path:
        if 'jobs-scraped-historic-for-training' not in csv_file_path:
            s3.download_file(
                ENV_BUCKET, csv_file_path, ge_data_full_path+csv_file_path.split('/')[-1])
    print("DOWNLOAD COMPLETE!")


####################################################################################################
# datasource_name = "jobs_datasource"
# dataconnector_name = "jobs_data_connector"

# Data Context
# context = DataContext(ge_directory_full_path)

# Data source
# if datasource_name in context.list_datasources():
# datasource = context.get_datasource(datasource_name)
# else:
#     datasource = context.sources.add_pandas_filesystem(
#         name=datasource_name, base_directory=ge_data_full_path)

# context.delete_datasource('jobs_datasource')

# Function to locally validate downloaded S3 data
def validate_s3_data():
    datasource_name = "s3local_datasource"
    dataconnector_name = "s3local_data_connector"
    # Data Context
    context = DataContext(ge_directory_full_path)

    datasource = context.get_datasource(datasource_name)
    # datasource = context.sources.add_pandas_filesystem(
    #     name=datasource_name, base_directory=ge_data_full_path)
    # Data Asset
    for csv in os.listdir(ge_data_full_path):
        name = f"{csv[:-4]}_asset"
        batching_regex = f"{csv[:-4]}\.csv"
        data_asset = datasource.add_csv_asset(
            name=name, batching_regex=batching_regex
        )

        batch_request = data_asset.build_batch_request()

        if f"{csv[:-4]}_expectation_suite.json" not in os.listdir(ge_expectations_full_path):
            validator = context.get_validator(
                batch_request=batch_request,
                create_expectation_suite_with_name=f"{csv[:-4]}_expectation_suite",
                # expectation_suite_name=f"{csv[:-4]}_expectation_suite",
            )
        elif f"{csv[:-4]}_expectation_suite.json" in os.listdir(ge_expectations_full_path):
            validator = context.get_validator(
                batch_request=batch_request,
                # create_expectation_suite_with_name=f"{csv[:-4]}_expectation_suite",
                expectation_suite_name=f"{csv[:-4]}_expectation_suite",
            )

        # Expectations
        validator.expect_table_row_count_to_be_between(
            min_value=0,
            max_value=30,
            result_format="COMPLETE"
        )
        validator.expect_column_values_to_not_be_null(column="Job ID")
        validator.expect_column_values_to_not_be_null(column="Title")
        validator.expect_column_values_to_not_be_null(column="Company")
        validator.expect_column_values_to_not_be_null(column="Date")
        validator.expect_column_values_to_not_be_null(column="Link")
        validator.expect_column_values_to_not_be_null(
            column="Description Length")
        validator.expect_column_values_to_not_be_null(column="Description")

        validator.expect_column_values_to_be_unique(column="Job ID")
        validator.expect_column_values_to_be_unique(column="Link")

        # link_regex = re.compile(
        #     r'^(https?|ftp):\/\/'  # protocol
        #     r'([a-zA-Z0-9]+:[a-zA-Z0-9]+@)?'  # username:password
        #     r'([a-zA-Z0-9]+(-[a-zA-Z0-9]+)*\.)+[a-zA-Z]{2,}'  # domain
        #     r'(:\d{1,5})?'  # port
        #     r'(\/[^\s]*)?'  # path
        #     r'(\?[^\s]*)?'  # query string
        #     r'(\#[^\s]*)?$'  # fragment
        # )

        # validator.expect_column_values_to_match_regex(
        #     column="Link", regex=link_regex)

        validator.expect_column_values_to_be_between(
            column="Description Length",
            min_value=0,
            max_value=10000,
            result_format="COMPLETE"
        )

        validator.save_expectation_suite(discard_failed_expectations=False)

        i = 1
        # Checkpoints
        while f"{csv[:-4]}_checkpointv0.{i}.json" in os.listdir(ge_checkpoints_full_path):
            i = i+1
        checkpoint = ge.checkpoint.SimpleCheckpoint(
            name=f"{csv[:-4]}_checkpointv0.{i}",
            data_context=context,
            validations=[
                {
                    "batch_request": batch_request,
                    "expectation_suite_name": f"{csv[:-4]}_expectation_suite",
                },
            ],
        )

        checkpoint_result = checkpoint.run()
        checkpoint_result_dict = checkpoint_result.to_json_dict()

        checkpoint_file_path = os.path.join(
            ge_checkpoints_full_path, f"{csv[:-4]}_checkpointv0.{i}.json")
        with open(checkpoint_file_path, "w") as f:
            json.dump(checkpoint_result_dict, f)

        context.build_data_docs()

# #########################################################################################################


def publishReport():
    for report in os.listdir(ge_datadocs_full_path):
        if report.endswith(".html"):
            s3.upload_file(ge_datadocs_full_path+report,
                           ENV_BUCKET, REPORT_PATH)

# DAG to download csv file from S3 bucket


dag = DAG(
    dag_id="s3JobsDag",
    schedule="0 0 * * *",   # https://crontab.guru/
    start_date=days_ago(0),
    catchup=False,
    # dagrun_timeout=timedelta(minutes=60),
    tags=["great_expectations", "AWS S3 Jobs Data",
          "S3DataScrape_Validate_ResultPublish"],
)

download_csv_files_operator = PythonOperator(
    task_id="download_csv_files",
    python_callable=download_csv_files,
    dag=dag,
)

validate_csv_files_operator = PythonOperator(
    task_id="validate_s3_data",
    python_callable=validate_s3_data,
    dag=dag,
)

publish_report_operator = PythonOperator(
    task_id="publish_s3_jobs_data_report",
    python_callable=publishReport,
    dag=dag,
)

# Dags Workflow
download_csv_files_operator >> validate_csv_files_operator >> publish_report_operator
