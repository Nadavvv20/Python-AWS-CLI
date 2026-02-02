import boto3
import os

# Creating the EC2 commands
class EC2Manager:
    def __init__(self):
        self.resource = boto3.resource('ec2')
        self.REGION  = "us-east-1"
        self.ALLOWED_AMIS = {
            "ubuntu" : "",
            "amazon-linux" : ""
        }
        self.ALLOWED_TYPES = ["t3.micro", "t3.small"]
        self.SECURITY_GROUP_IDS = ['sg-00573ff68f2148855']
        self.KEY_NAME = "Nadav-CLI-Project-Key.pem"
        self.LIMIT = 2
        
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

    def create_instance(self, instance_type, ami):
        # Validating the parameters
        self._validate_inputs(instance_type, ami)

        # Checking the amount of instances:
        if not self.is_quota_available():
            print(f"❌ Error: You cannot have more than {self.LIMIT} instances.")
            return

        # Creation of the instance:
        print("🚀 Creating instance...")
        try: 
            instances = self.resource.create_instances(
                ImageId = self.ALLOWED_AMIS[ami],
                InstanceType = instance_type,
                KeyName = self.KEY_NAME,
                SecurityGroupIds = self.SECURITY_GROUP_IDS,
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {'Key': 'CreatedBy', 'Value': 'Nadav-platform-cli'}
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
