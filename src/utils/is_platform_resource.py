import boto3
from rich.console import Console
console = Console()

def is_platform_resource(bucket_name):
    s3_client = boto3.client('s3')
    try:
        # Get the tags of the bucket
        response = s3_client.get_bucket_tagging(Bucket=bucket_name)
        tag_set = {tag['Key']: tag['Value'] for tag in response['TagSet']}
        
        # Check if the tag exists
        return tag_set.get('CreatedBy') == 'Nadav-Platform-CLI'
        
    except Exception:
        console.print(f"[bold red]❌ Access Denied:[/bold red] Bucket '{bucket_name}' has no tags.")
        return False