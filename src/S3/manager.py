import boto3
import os
from src.utils.helpers import console, progress_spinner, get_aws_user, is_platform_resource

current_user = get_aws_user()
my_tags = {"CreatedBy": "Nadav-Platform-CLI", "Owner": current_user}

def create_bucket(bucket_name, region = 'us-east-1', is_public = False):
    try:
        # Confirmation for public bucket BEFORE creation
        if is_public:
            verification = input(f"⚠️  Are you sure you want to create a PUBLIC bucket '{bucket_name}'? (yes/no): ")
            if verification.lower() not in ["yes", "y"]:
                console.print("[yellow]✋ Public creation cancelled. Defaulting to PRIVATE bucket.[/yellow]")
                is_public = False
        
        bucket_config = {}
        # LocationConstraint is required for regions other than us-east-1
        if region != 'us-east-1':
             bucket_config = {'LocationConstraint': region}

        s3_client = boto3.client('s3', region_name=region)
        
        if region == 'us-east-1':
            s3_client.create_bucket(Bucket=bucket_name)
        else:
            s3_client.create_bucket(Bucket=bucket_name, CreateBucketConfiguration=bucket_config)

        console.print(f"[green]✅ Bucket '{bucket_name}' created successfully in {region}.[/green]")
        
        # Add the tags to the bucket
        tag_set = [{'Key': k, 'Value': v} for k, v in my_tags.items()]
        s3_client.put_bucket_tagging(
                Bucket=bucket_name,
                Tagging={'TagSet': tag_set}
            )

        # Configure Access
        if is_public:
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
            console.print("[bold yellow][blink]⚠️[/blink]  Bucket is configured to ALLOW public access.[/bold yellow]")
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
            console.print("[blue]🔒 Bucket is set to Private.[/blue]")

        return True
    except Exception as e:
        console.print(f"[bold red]❌ Error in creating a bucket:[/bold red] {e}")
        return False

def cleanup_s3_resources():
    s3_client = boto3.client('s3')
    s3_resource = boto3.resource('s3')
    
    try:
        response = s3_client.list_buckets()
        found_any = False
        
        with progress_spinner("Checking S3 buckets for cleanup..."):
            for bucket_data in response.get('Buckets', []):
                bucket_name = bucket_data['Name']
                
                if is_platform_resource(bucket_name):
                    found_any = True
                    console.print(f"  🗑️  Found platform bucket: [cyan]{bucket_name}[/cyan]")
                    
                    bucket = s3_resource.Bucket(bucket_name)
                    
                    # Delete all objects first
                    bucket.objects.all().delete()
                    # Delete versions if enabled (optional but good practice)
                    bucket.object_versions.all().delete()
                    
                    # Delete the bucket
                    bucket.delete()
                    console.print(f"     ✅ Deleted bucket: [strike red]{bucket_name}[/strike red]")
        
        if not found_any:
            console.print("[green]✨ No platform S3 buckets found to clean.[/green]")
            
    except Exception as e:
        console.print(f"[bold red]❌ Error during S3 cleanup:[/bold red] {e}")

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
