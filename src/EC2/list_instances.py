import boto3

ec2 = boto3.client('ec2', region_name='us-east-1')

def list_instances():
    response = ec2.describe_instances(
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
    
    instances = []
    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instances.append(instance)
            
    return instances


    