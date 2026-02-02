import boto3

ec2 = boto3.resource('ec2', region_name='us-east-1')

def list_instances():
    instances = ec2.instances.filter(
            Filters=[
                {
                    'Name': 'tag:CreatedBy',
                    'Values': ['Nadav-Platform-CLI']
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['running', 'pending', 'stopping', 'stopped']
                }
            ]
        )
    