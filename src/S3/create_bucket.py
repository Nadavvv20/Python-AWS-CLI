import boto3

def create_bucket(bucket_name, region='us-east-1'):
    try:
        bucket_config = {}
        s3_client = boto3.client('s3', region_name=region)
        s3_client.create_bucket(Bucket=bucket_name, **bucket_config)
    except Exception as e:
        print(f"Error in creating a bucket: {e}")
        return False
    return True