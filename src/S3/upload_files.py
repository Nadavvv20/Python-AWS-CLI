import boto3
import os
from src.utils.ui_helper import console
from src.utils.is_platform_resource import is_platform_resource

def upload_files(file_name, bucket_name, object_name=None):
    # Check if the bucket is made by the CLI platform
    if not is_platform_resource(bucket_name):
        console.print(f"[bold red]❌ Access Denied:[/bold red] Bucket '{bucket_name}' does not have the required platform tags.")
        return False

     # If S3 object_name was not specified, use file_name
    if object_name is None:
        object_name = os.path.basename(file_name)

    s3_client = boto3.client('s3')
    try:
        with console.status(f"[bold green]Uploading {file_name} to {bucket_name}...[/bold green]"):
            s3_client.upload_file(file_name, bucket_name, object_name)
        console.print(f"✅ File uploaded successfully to [blue]{bucket_name}[/blue]")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Upload failed:[/bold red] {e}")
        return False