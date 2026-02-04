import click
from src.ec2.manager import list_instances, EC2Creator, cleanup_ec2_resources
from src.s3.manager import create_bucket, upload_files, list_buckets, cleanup_s3_resources
from src.route53.manager import create_hosted_zones, list_my_dns, manage_dns_record, cleanup_dns_resources


@click.group()
def main_cli():
    """AWS Control CLI - Nadav's Platform Tool"""
    
    pass

# --- EC2 Group ---
@main_cli.group()
def ec2():
    """Manage EC2 resources"""
    pass

@ec2.command(name="list")
def ec2_list():
    """List platform instances"""
    list_instances()

@ec2.command(name="create")
@click.option("--name", required=True, help="Instance name tag")
@click.option("--ami", default="ubuntu", help="AMI alias (ubuntu/amazon-linux)")
@click.option("--type", "instance_type", default="t3.micro", help="Instance type (t3.micro/t3.small)")
def ec2_create(name, ami, instance_type):
    """Create a new EC2 instance"""
    creator = EC2Creator()
    creator.create_instance(ami_input=ami, instance_type_input=instance_type, instance_name_input=name)

@ec2.command(name="cleanup")
def ec2_cleanup():
    """Terminate all platform instances"""
    cleanup_ec2_resources()

# --- S3 Group ---
@main_cli.group()
def s3():
    """Manage S3 resources"""
    pass

@s3.command(name="create")
@click.option("--name", required=True, help="Bucket name")
@click.option("--public", "privacy", flag_value="public", help="Make bucket public")
@click.option("--private", "privacy", flag_value="private", default=True, help="Make bucket private (default)")
def s3_create(name, privacy):
    """Create a new S3 bucket"""
    is_public = (privacy == "public")
    create_bucket(bucket_name=name, is_public=is_public)

@s3.command(name="upload")
@click.option("--bucket", required=True, help="Target bucket name")
@click.option("--file", "file_path", required=True, help="Local file path")
@click.option("--key", required=False, help="S3 object key")
def s3_upload(bucket, file_path, key):
    """Upload file to S3"""
    # upload_files signature: file_name, bucket_name, object_name=None
    upload_files(file_name=file_path, bucket_name=bucket, object_name=key)
@s3.command(name="list")
def s3_list():
    """ List S3 buckets """
    list_buckets()

@s3.command(name="cleanup")
def s3_cleanup():
    """Delete all platform buckets"""
    cleanup_s3_resources()

# --- DNS Group ---
@main_cli.group()
def dns():
    """Manage Route53 resources"""
    pass

@dns.command(name="list")
def dns_list():
    """List platform DNS zones and records"""
    list_my_dns()

@dns.command(name="create-zone")
@click.argument("domain")
def dns_create_zone(domain):
    """Create a new Hosted Zone"""
    create_hosted_zones(domain)

@dns.command(name="record")
@click.argument("zone_id")
@click.argument("action", type=click.Choice(['UPSERT', 'DELETE']))
@click.option("--name", required=True, help="Record Name")
@click.option("--type", "record_type", required=True, help="Record Type (A, CNAME, TXT...)")
@click.option("--value", required=True, help="Record Value")
def dns_record(zone_id, action, name, record_type, value):
    """Manage DNS records"""
    manage_dns_record(zone_id, action, name, record_type, value)

@dns.command(name="cleanup")
def dns_cleanup():
    """Delete all platform hosted zones"""
    cleanup_dns_resources()

if __name__ == "__main__":
    main_cli()