import boto3
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

        
    def _validate_inputs(self, instance_type, ami):
        if ami not in self.ALLOWED_AMIS:
            raise ValueError(f"This AMI is not valid - You can choose: {self.ALLOWED_AMIS}")
        if instance_type not in self.ALLOWED_TYPES:
            raise   ValueError(f"This type is not valid - You are allowed to create only \
{self.ALLOWED_TYPES}")

        
    def create_instance(self, instance_type, ami):
        # Validating the parameters
        self._validate_inputs(instance_type, ami)
        try: 
            instances = self.resource.create_instances(
                ImageId = self.ALLOWED_AMIS[ami],
                InstanceType = instance_type,
                KeyName = self.KEY_NAME,
                SecurityGroupIds = self.SECURITY_GROUP_IDS

            )
