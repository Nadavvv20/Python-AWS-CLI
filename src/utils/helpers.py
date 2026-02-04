from rich.panel import Panel
import boto3
from rich.console import Console
import pyfiglet
from contextlib import contextmanager
import time

console = Console()

def get_aws_user():
    # Get the name of the current AWS user
    sts = boto3.client('sts')
    try:
        identity = sts.get_caller_identity()
        return identity['Arn'].split('/')[-1]
    except Exception:
        return "Unknown-User"

def is_platform_resource(bucket_name):
    s3_client = boto3.client('s3')
    try:
        # Get the tags of the bucket
        response = s3_client.get_bucket_tagging(Bucket=bucket_name)
        tag_set = {tag['Key']: tag['Value'] for tag in response['TagSet']}
        
        # Check if the tag exists
        return tag_set.get('CreatedBy') == 'Nadav-Platform-CLI'
        
    except Exception:
        return False

@contextmanager
def progress_spinner(message="Working..."):
    with console.status(f"[bold blue]⏳ {message}", spinner="dots"):
        yield

