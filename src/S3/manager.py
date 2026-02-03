import boto3
import os
from src.utils.helpers import console, progress_spinner, get_aws_user, is_platform_resource

current_user = get_aws_user()
my_tags = {"CreatedBy": "Nadav-Platform-CLI", "Owner": current_user}

def create_bucket(bucket_name, region = 'us-east-1', is_public = False):
    try:
        bucket_config = {}
        s3_client = boto3.client('s3', region_name=region)
        s3_client.create_bucket(Bucket=bucket_name, **bucket_config)
        console.print(f"[green]✅ Bucket '{bucket_name}' created successfully in {region}.[/green]")
        # Add the tags to the bucket
        tag_set = [{'Key': k, 'Value': v} for k, v in my_tags.items()]
        s3_client.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={'TagSet': tag_set}
            )

        if is_public:
            verification = input("Are you sure you want the bucket to be public? (yes/no)")
            if verification in ["yes", "y", "Y", "YES"]:
                print("Configuring public access...")
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': False,
                        'IgnorePublicAcls': False,
                        'BlockPublicPolicy': False,
                        'RestrictPublicBuckets': False
                    }
                )
                console.print("[bold yellow]⚠️ Warning: Bucket is now configured to ALLOW public access.[/bold yellow]")
            else:
                print("Configuring private bucket...")
                s3_client.put_public_access_block(
                    Bucket=bucket_name,
                    PublicAccessBlockConfiguration={
                        'BlockPublicAcls': True,
                        'IgnorePublicAcls': True,
                        'BlockPublicPolicy': True,
                        'RestrictPublicBuckets': True
                    }
                )
                console.print("[blue]🔒 Bucket is set to Private (Block Public Access enabled).[/blue]")

        return True
    except Exception as e:
        console.print(f"[bold red]❌ Error in creating a bucket:[/bold red] {e}")
        return False

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
