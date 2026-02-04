import sys
import os
import uuid
import time
import boto3

# Add project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.s3.manager import create_bucket, upload_files, list_buckets, cleanup_s3_resources
from src.utils.helpers import console

def test_s3_flow():
    # 1. Setup
    bucket_name = f"test-bucket-{uuid.uuid4()}"
    file_name = "hello_s3.txt"
    file_content = "Hello, S3! This is a test upload."
    
    # Create a dummy file in the current directory
    with open(file_name, "w") as f:
        f.write(file_content)
        
    console.print(f"[bold blue]--- Starting S3 Flow Test for {bucket_name} ---[/bold blue]")

    try:
        # 2. Create Bucket
        console.print(f"\n[bold]1. Testing Create Bucket: {bucket_name}[/bold]")
        # create_bucket(bucket_name, region, is_public) - defaults are fine
        created = create_bucket(bucket_name)
        
        if not created:
            raise Exception("Create bucket returned False.")
        
        console.print("   Waiting for consistency...")
        time.sleep(2)

        # 3. Upload File
        console.print(f"\n[bold]2. Testing Upload File: {file_name}[/bold]")
        uploaded = upload_files(file_name, bucket_name)
        
        if not uploaded:
             raise Exception("File upload returned False.")

        console.print("\n✅ Bucket created and file uploaded successfully.", style="bold green")
        
        # 4. List Buckets
        console.print("\n[bold]3. Listing buckets:[/bold]")
        list_buckets()

        console.print("\n✅ S3 Flow Test Passed Successfully.", style="bold green")

    except Exception as e:
        console.print(f"\n[bold red]❌ Test Failed:[/bold red] {e}")

    finally:
        # 5. Cleanup
        console.print("\n[bold]4. Cleaning up resources...[/bold]")
        
        # Use simple boto3 to verify/delete local file
        if os.path.exists(file_name):
            os.remove(file_name)
            console.print(f"   Deleted local file {file_name}")

        # Use the platform cleanup function
        cleanup_s3_resources()

if __name__ == "__main__":
    test_s3_flow()
