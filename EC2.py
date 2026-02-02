import boto3
VALID_TYPES = ["t3.micro", "t3.small"]
AMI = ["latest ubuntu", "latest amazon linux"]
ec2 = boto3.resource('ec2', region_name='us-east-1')

def instanceCreate(instance_type, instance_ami):
    try:
        instances: ec2.create_in