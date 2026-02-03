import boto3
import sys
import os
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui_helper import progress_spinner
from src.utils.is_platform_resource import is_platform_resource

def list_buckets():

    s3 = boto3.client('s3')
    response = s3.list_buckets()
    
    # This variable indicates whether there are buckets that was made by Nadav-Platform-CLI or not.
    # If at least 1 bucket was found, this will be changed to 'True'
    bucket_found = False

    with progress_spinner("Listing Buckets made with the CLI Platform, \n     this might take a few seconds..."):
        for bucket in response['Buckets']:
            if is_platform_resource(bucket["Name"]):
                print(f'  {bucket["Name"]}')
                bucket_found = True
    if not bucket_found:
        print("No buckets were found.")

if __name__ == "__main__":
    list_buckets()
