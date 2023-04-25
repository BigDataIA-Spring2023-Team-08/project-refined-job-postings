import boto3
from pydotenvs import load_env
import os

load_env()

def upload_to_s3(file, filename):
    """ 
    Uploads a file to an Amazon S3 bucket.
    
    Input Parameters:
    file : UploadFile
         The file to upload.
    filename : str
        The name to give to the uploaded file.
    ----
    Returns:
    None: The function does not return anything.
    -----
    Raises:
        botocore.exceptions.NoCredentialsError: If the AWS access key and secret key are not set in the environment.
    """
    s3 = boto3.client('s3')
    access_key_id = os.environ.get("AWS_ACCESS_KEY")
    aws_secret_key_id = os.environ.get("AWS_SECRET_KEY_ID")
    bucket_name = os.environ.get("YOUR_BUCKET_NAME")
    region = os.environ.get("AWS_REGION")
    s3 = boto3.client('s3', region_name=region, aws_access_key_id=access_key_id, aws_secret_access_key=aws_secret_key_id)

    s3.upload_fileobj(file.file, bucket_name, filename)