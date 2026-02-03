import boto3
from src.utils.ui_helpers import console


def upload_files(bucket_name, file_path, key):
    s3 = boto3.resource('s3')

    # Need to filter only those with the "CreatedBy tag"
    s3.bucket(bucket_name).upload_file(file_path, key)