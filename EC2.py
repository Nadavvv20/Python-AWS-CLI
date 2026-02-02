import boto3
import os

# Creating the EC2 commands
class EC2Manager:
    def __init__(self):
        # Resource definition 
        self.resource = boto3.resource('ec2', region_name='us-east-1')
        self.ssm = boto3.client('ssm', region_name='us-east-1')
        self.sts = boto3.client('sts')

        # Amis list
        self.ALLOWED_AMIS = {
            "ubuntu" : "/aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami_id",
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
            print(f"❌ Could not fetch AMI from SSM: {str(e)}")
            return None



    def _validate_inputs(self, instance_type, ami):
        if ami not in self.ALLOWED_AMIS:
            raise ValueError(f"This AMI is not valid - You can choose: {list(self.ALLOWED_AMIS.keys())}")
        if instance_type not in self.ALLOWED_TYPES:
            raise ValueError(f"This type is not valid - You are allowed to create only {self.ALLOWED_TYPES[0]} or {self.ALLOWED_TYPES[1]}")

    def is_quota_available(self):
        print("Checking instances created by Nadav-platform-cli...")
        # Filtering for instances with the specific tag AND that are not terminated
        instances = self.resource.instances.filter(
            Filters=[
                {
                    'Name': 'tag:CreatedBy',
                    'Values': ['Nadav-platform-cli']
                },
                {
                    'Name': 'instance-state-name',
                    'Values': ['running', 'pending', 'stopping', 'stopped']
                }
            ]
        )
        count = len(list(instances))
        print(f"Found {count} instances.")
        
        if count >= self.LIMIT:
            return False
        return True

    def create_instance(self, instance_type_input, ami_input, instance_name_input):
        # Validating the parameters
        self._validate_inputs(instance_type_input, ami_input)

        try:
            identity = self.sts.get_caller_identity()
            # Get the aws user name
            aws_user = identity['Arn'].split('/')[-1]
        except Exception as e:
            print(f"⚠️ Warning: Could not detect AWS user, using 'unknown'. Error: {e}")
            aws_user = "unknown"

        # Get the ami id
        ami_id = self.get_latest_ami_id(ami_input)
        # If coudn't manage to get the ami id:
        if not ami_id:
            return

        # Checking the amount of instances:
        if not self.is_quota_available():
            print(f"❌ Error: You cannot have more than {self.LIMIT} instances.")
            return

        # Creation of the instance:
        print("🚀 Creating instance...")
        try: 
            instances = self.resource.create_instances(
                ImageId = ami_id,
                InstanceType = instance_type_input,
                KeyName = self.KEY_NAME,
                SecurityGroupIds = self.SECURITY_GROUP_IDS,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'Name', 'Value': instance_name_input},
                            {'Key': 'CreatedBy', 'Value': 'Nadav-platform-cli'},
                            {'Key': 'Owner', 'Value': aws_user},
                        ]
                    }
                ],
                MinCount=1,
                MaxCount=1
            )
            new_instance = instances[0]
            print("⏳ Waiting for instance to be running...")
            new_instance.wait_until_running()
            print("✅ Instance is up and running!")
            print(f"Instance Id: {new_instance.id}")

        except Exception as e:
            print(f"An error occured: {e}")
