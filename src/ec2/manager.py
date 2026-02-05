import boto3
import sys
import os
from src.utils.helpers import console, progress_spinner, get_aws_user

# Accessing the EC2 service in us-east-1 region
ec2 = boto3.client('ec2', region_name='us-east-1')

def list_instances():
    with progress_spinner("Listing instances..."):
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
                print(instance['InstanceId'])
        if not instances:
            console.print("[yellow]⚠️  No instances found matching your criteria (Tag: CreatedBy=Nadav-Platform-CLI).[/yellow]")
            return

def change_instance_state(instance_id, action):
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

    print("Checking instance tags...")
    if any(i['InstanceId'] == instance_id for i in instances):
        print("Instance has the correct tags.")
        print(f"Attempting to {action} instance: {instance_id}")
        try:
            if action == "stop":
                ec2.stop_instances(InstanceIds=[instance_id])
                with progress_spinner("Stopping instance..."):
                    waiter = ec2.get_waiter('instance_stopped')
                    waiter.wait(InstanceIds=[instance_id])
                print(f"✅ Instance {instance_id} is now fully stopped!")
            elif action == "start":
                ec2.start_instances(InstanceIds=[instance_id])
                with progress_spinner("Starting instance..."):
                    waiter = ec2.get_waiter('instance_running')
                    waiter.wait(InstanceIds=[instance_id])
                print(f"✅ Instance {instance_id} is now running!")
            else:
                print("❌ Error: This action is not recognized. Please consult with your DevOps team.")
                return
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return
    else:
        print("❌ Error: This instance doesn't have the right tag or is terminated")
        return


# Creating the EC2 create command
class EC2Creator:
    def __init__(self):
        # Resource definition 
        self.client = boto3.client('ec2', region_name='us-east-1')
        self.ssm = boto3.client('ssm', region_name='us-east-1')
        self.sts = boto3.client('sts')

        # Amis list
        self.ALLOWED_AMIS = {
            "ubuntu" : "/aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id",
            "amazon-linux" : "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
        }

        # Limits and configurations
        self.ALLOWED_TYPES = ["t3.micro", "t3.small"]
        self.LIMIT = 2

        # Security
        self.SECURITY_GROUP_IDS = ['sg-00573ff68f2148855']
        self.KEY_NAME = "Nadav-CLI-Project-Key"
        
    def get_latest_ami_id(self, ami_name):
        # Check if the user's input ami is in the allowed amis list
        if ami_name not in self.ALLOWED_AMIS:
            print(f"❌ Error: {ami_name} is not a supported OS. Choose from: {list(self.ALLOWED_AMIS.keys())}")
            return None

        # Get the path for the ami to look for in the parameter store
        parameter_path = self.ALLOWED_AMIS[ami_name]

        try:
            # Looking for the ami-id in the SSM Parameter Store
            response = self.ssm.get_parameter(Name=parameter_path)
            ami_id = response['Parameter']['Value']
            
            print(f"🔍 Successfully resolved {ami_name} to: {ami_id}")
            return ami_id

        except Exception as e:
            print(f"❌ Could not fetch AMI {ami_name} from SSM: {str(e)}")
            return



    def _validate_inputs(self, instance_type, ami):
        if ami not in self.ALLOWED_AMIS:
            raise ValueError(f"❌ This AMI is not valid - You can choose: {list(self.ALLOWED_AMIS.keys())}")
        if instance_type not in self.ALLOWED_TYPES:
            raise ValueError(f"❌ This type is not valid - You are allowed to create only {self.ALLOWED_TYPES[0]} or {self.ALLOWED_TYPES[1]}")

    def is_quota_available(self):
        print("Checking instances created by Nadav-Platform-CLI...")
        # Filtering for instances with the specific tag AND that are not terminated
        response = self.client.describe_instances(
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
        
        count = 0
        for reservation in response.get('Reservations', []):
            count += len(reservation.get('Instances', []))

        print(f"Found {count} instances.")
        
        if count >= self.LIMIT:
            return False
        return True

    def create_instance(self, ami_input, instance_type_input, instance_name_input):
        # Validating the parameters
        self._validate_inputs(instance_type_input, ami_input)
        
        # Get the aws user name
        aws_user = get_aws_user()

        # Get the ami id
        ami_id = self.get_latest_ami_id(ami_input)
        # If couldn't manage to get the ami id:
        if not ami_id:
            return

        # Checking the amount of instances:
        if not self.is_quota_available():
            print(f"❌ Error: You cannot have more than {self.LIMIT} instances.")
            return

        # Creation of the instance:
        # Creation of the instance:
        try: 
            with progress_spinner("Creating instance..."):
                response = self.client.run_instances(
                    ImageId = ami_id,
                    InstanceType = instance_type_input,
                    KeyName = self.KEY_NAME,
                    SecurityGroupIds = self.SECURITY_GROUP_IDS,
                    TagSpecifications=[
                        {
                            'ResourceType': 'instance',
                            'Tags': [
                                {'Key': 'Name', 'Value': instance_name_input},
                                {'Key': 'CreatedBy', 'Value': 'Nadav-Platform-CLI'},
                                {'Key': 'Owner', 'Value': aws_user},
                            ]
                        }
                    ],
                    MinCount=1,
                    MaxCount=1
                )
                new_instance_id = response['Instances'][0]['InstanceId']
            
            with progress_spinner("Waiting for instance to be running..."):
                waiter = self.client.get_waiter('instance_running')
                waiter.wait(InstanceIds=[new_instance_id])
            
            print("✅ Instance is up and running!")
            return(f"Instance Id: {new_instance_id}")
        

        except Exception as e:
            print(f"An error occured: {e}")

def cleanup_ec2_resources():
    ec2 = boto3.client('ec2', region_name='us-east-1')
    try:
        # Find instances
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
        
        instance_ids = []
        for reservation in response.get('Reservations', []):
            for instance in reservation.get('Instances', []):
                instance_ids.append(instance['InstanceId'])
        
        if not instance_ids:
            console.print("[green]✨ No platform EC2 instances found to clean.[/green]")
            return

        console.print(f"[yellow]🗑️  Found {len(instance_ids)} instances to clean: {', '.join(instance_ids)}[/yellow]")
        
        # Terminate
        ec2.terminate_instances(InstanceIds=instance_ids)
        
        with progress_spinner(f"Terminating {len(instance_ids)} instances..."):
            waiter = ec2.get_waiter('instance_terminated')
            waiter.wait(InstanceIds=instance_ids)
            
        console.print(f"[green]✅ Successfully terminated {len(instance_ids)} instances.[/green]")

    except Exception as e:
        console.print(f"[bold red]❌ Error during EC2 cleanup:[/bold red] {e}")
