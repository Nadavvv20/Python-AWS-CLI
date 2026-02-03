import sys
import os
import uuid
import time
import boto3

# Add project root to sys.path so we can import src modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.S3.create_bucket import create_bucket
from src.S3.upload_files import upload_files

def test_s3_flow():
    # 1. Setup
    bucket_name = f"test-bucket-{uuid.uuid4()}"
    file_name = "hello_s3.txt"
    file_content = "Hello, S3! This is a test upload."
    
    # Create a dummy file in the current directory
    with open(file_name, "w") as f:
        f.write(file_content)
        
    try:
        # 2. Create Bucket
        print(f"\n--- Testing Create Bucket: {bucket_name} ---")
        # create_bucket(bucket_name, region, is_public) - defaults are fine
        created = create_bucket(bucket_name)
        
        if not created:
            print("❌ Create bucket returned False. Stopping test.")
            return

        print("Waiting for consistency...")
        time.sleep(2)

        # 3. Upload File
        print(f"\n--- Testing Upload File: {file_name} ---")
        uploaded = upload_files(file_name, bucket_name)
        
        if uploaded:
            print("\n✅ TEST PASSED: Bucket created and file uploaded successfully.")
        else:
            print("\n❌ TEST FAILED: File upload returned False.")

    finally:
        # 4. Cleanup
        print("\n--- Cleaning up resources ---")
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        try:
            # Check if bucket exists first to avoid 404
            if bucket.creation_date:
                bucket.objects.all().delete()
                bucket.delete()
                print(f"Bucket {bucket_name} deleted.")
            else:
                print(f"Bucket {bucket_name} does not exist, skipping cleanup.")
        except Exception as e:
            print(f"Note during cleanup: {e}")
        
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"File {file_name} removed.")

if __name__ == "__main__":
    test_s3_flow()
