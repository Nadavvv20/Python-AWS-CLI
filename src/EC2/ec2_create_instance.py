import boto3
import os
import sys
# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.ui_helpers import progress_spinner
from rich.console import Console
from src.utils.aws_identity import get_aws_user
console = Console()
console.print(":cloud: [bold blue]Connecting to AWS...[/bold blue]")

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
