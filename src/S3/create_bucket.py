import boto3
from src.utils.ui_helpers import console
from src.utils.aws_identity import get_aws_user

current_user = get_aws_user()
my_tags = {"CreatedBy": "Nadav", "Owner": current_user}
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
