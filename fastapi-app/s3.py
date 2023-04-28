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

    #read the environment variables
    access_key_id = os.environ.get("AWS_ACCESS_KEY")
    aws_secret_key_id = os.environ.get("AWS_SECRET_KEY")
    user_bucket = os.environ.get("USER_BUCKET_NAME")
    
    #set up the boto3 client
    s3client = boto3.client('s3', 
                            region_name='us-east-1', 
                            aws_access_key_id=access_key_id, 
                            aws_secret_access_key=aws_secret_key_id)
            
    s3_path = f'dataset/user-uploads/{filename}'    #path on s3 bucket
    s3client.upload_fileobj(file.file, user_bucket, s3_path)    #upload the file to s3
    #return True

def check_resume_on_s3(username, filename):
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

    #read the environment variables
    access_key_id = os.environ.get("AWS_ACCESS_KEY")
    aws_secret_key_id = os.environ.get("AWS_SECRET_KEY")
    user_bucket = os.environ.get("USER_BUCKET_NAME")
    
    #set up the boto3 client
    s3resource = boto3.resource('s3', 
                            region_name='us-east-1', 
                            aws_access_key_id=access_key_id, 
                            aws_secret_access_key=aws_secret_key_id)
    i=0
    for objects in s3resource.Bucket(user_bucket).objects.filter(Prefix='dataset/user-uploads/'):   #traverse through the files found on the S3 bucket batch folder
        if(i==0):
            pass    #since the first object is the root directory object, we do not need this so pass
        else:
            if (objects.key.split("/")[-1] == filename):
                return True
        i+=1    #being used to check for first object, could also use a boolean flag

    return False
    