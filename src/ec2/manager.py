import boto3
import sys
import os
from src.utils.helpers import console, progress_spinner, get_aws_user
from click import ClickException
from botocore.exceptions import ClientError

# Accessing the EC2 service in us-east-1 region
ec2 = boto3.client('ec2', region_name='us-east-1')

def get_instances():
    """
    Returns a list of EC2 instance dictionaries created by the platform.
    """
    response = ec2.describe_instances(
        Filters=[
            {
                'Name': 'tag:CreatedBy',
                'Values': ['Nadav-Platform-CLI']
            },
            {
                'Name': 'instance-state-name',
                'Values': ['running', 'pending', 'stopping', 'stopped', 'shutting-down']
            }
        ]
    )
    
    instances = []
    for reservation in response.get('Reservations', []):
        for instance in reservation.get('Instances', []):
            instances.append(instance)
    return instances

def get_security_groups():
    """
    Returns a list of Security Group dictionaries created by the platform.
    """
    response = ec2.describe_security_groups(
        Filters=[
            {
                'Name': 'tag:CreatedBy',
                'Values': ['Nadav-Platform-CLI']
            }
        ]
    )
    return response.get('SecurityGroups', [])

def delete_security_groups(group_ids=None):
    """
    Deletes the provided security groups. If no IDs are provided, it fetches all platform-created security groups.
    """
    if group_ids is None:
        console.print("[dim]No security group IDs provided. Scanning for all platform security groups...[/dim]")
        sgs = get_security_groups()
        group_ids = [sg['GroupId'] for sg in sgs]

    if not group_ids:
        console.print("[green]✨ No security groups to delete.[/green]")
        return

    console.print(f"[yellow]🛡️  Found {len(group_ids)} security groups to clean...[/yellow]")
    
    for sg_id in group_ids:
        try:
            ec2.delete_security_group(GroupId=sg_id)
            print(f"✅ Deleted Security Group: {sg_id}")
        except ClientError as e:
            if 'DependencyViolation' in str(e):
                print(f"⚠️  Could not delete {sg_id}: Dependency Violation (Likely still attached to a terminating instance).")
            else:
                print(f"❌ Error deleting {sg_id}: {e}")

def list_instances():
    with progress_spinner("Listing instances..."):
        instances = get_instances()
        
        if not instances:
            console.print("[yellow]⚠️  No instances found matching your criteria (Tag: CreatedBy=Nadav-Platform-CLI).[/yellow]")
            return

        for instance in instances:
            print(instance['InstanceId'])

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
            "ubuntu" : "/aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id",
            "amazon-linux" : "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
        }

        # Limits and configurations
        self.ALLOWED_TYPES = ["t3.micro", "t3.small"]
        self.LIMIT = 2

        
    def ensure_key_pair(self, key_name):
        """
        Checks if a key pair exists. If not, creates it and saves the .pem file.
        """
        try:
            self.client.describe_key_pairs(KeyNames=[key_name])
            print(f"🔑 Key Pair '{key_name}' found. Using existing key.")
            return key_name
        except ClientError as e:
            if 'InvalidKeyPair.NotFound' in str(e):
                print(f"⚠️  Key Pair '{key_name}' not found. Creating it...")
                try:
                    key_pair = self.client.create_key_pair(KeyName=key_name, KeyType='rsa')
                    private_key = key_pair['KeyMaterial']
                    
                    # Save the private key to a file
                    file_name = f"{key_name}.pem"
                    with open(file_name, "w") as f:
                        f.write(private_key)
                    
                    # Set permissions (read-only for owner) - Windows specific handling might be needed but simple write is fine for now
                    # os.chmod(file_name, 0o400) 
                    
                    print(f"✅ Key Pair created! Private key saved to: {os.path.abspath(file_name)}")
                    print("⚠️  IMPORTANT: Keep this file safe. You will not be able to download it again.")
                    return key_name
                except Exception as create_error:
                    print(f"❌ Failed to create key pair: {create_error}")
                    return None
            else:
                print(f"❌ Error checking key pair: {e}")
                return None

    def create_security_group(self, group_name, description="Created by Nadav-Platform-CLI"):
        """
        Creates a security group allowing SSH from anywhere.
        """
        try:
            # Check if SG already exists to avoid duplication errors
            # Check if SG already exists to avoid duplication errors
            existing_sgs = self.client.describe_security_groups(
                Filters=[
                    {'Name': 'group-name', 'Values': [group_name]},
                    {'Name': 'tag:CreatedBy', 'Values': ['Nadav-Platform-CLI']}
                ]
            )
            if existing_sgs['SecurityGroups']:
                sg_id = existing_sgs['SecurityGroups'][0]['GroupId']
                print(f"🛡️  Security Group '{group_name}' ({sg_id}) already exists. Using it.")
                return sg_id

            print(f"🛡️  Creating Security Group '{group_name}'...")
            response = self.client.create_security_group(
                GroupName=group_name,
                Description=description
            )
            security_group_id = response['GroupId']
            
            # Add Inbound Rule (SSH Port 22 from 0.0.0.0/0)
            self.client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            )
            
            # Tag the Security Group
            self.client.create_tags(
                Resources=[security_group_id],
                Tags=[
                    {'Key': 'Name', 'Value': group_name},
                    {'Key': 'CreatedBy', 'Value': 'Nadav-Platform-CLI'}
                ]
            )
            
            print(f"✅ Security Group created: {security_group_id} (Port 22 Open)")
            return security_group_id

        except ClientError as e:
            if 'InvalidGroup.Duplicate' in str(e):
                print(f"❌ Error: Security Group '{group_name}' already exists but is missing the 'CreatedBy' tag.")
                print("   Please delete the existing group manually or use a different name.")
                return None
            print(f"❌ Error creating security group: {e}")
            return None
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
            raise ClickException(f"❌ This AMI is not valid - You can choose: {list(self.ALLOWED_AMIS.keys())}")
        if instance_type not in self.ALLOWED_TYPES:
            raise ClickException(f"❌ This type is not valid - You are allowed to create only {self.ALLOWED_TYPES[0]} or {self.ALLOWED_TYPES[1]}")

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

    def create_instance(self, ami_input, instance_type_input, instance_name_input, key_input):
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

        # Ensure Key Pair exists
        key_name = self.ensure_key_pair(key_input)
        if not key_name:
            return

        # Ensure Security Group exists
        # Use a consistent naming convention for the SG, or per-instance. 
        # Per user request: "a new sg group will be created automatticaly... the new sg will have the 'CreatedBy' tag"
        # Since we want to allow potentially multiple instances, sharing an SG is usually better practice, 
        # but to follow "creating an ec2, a new sg group" strictly, we could make it per instance.
        # However, making it per instance might clutter. 
        # Let's create one unique per instance name to satisfy "new sg group" per creation flow implies specific to this deployment.
        # Let's create one unique per instance name to satisfy "new sg group" per creation flow implies specific to this deployment.
        sg_name = "Nadav-CLI-SG"
        security_group_id = self.create_security_group(sg_name)
        if not security_group_id:
            return

        # Creation of the instance:
        # Creation of the instance:
        try: 
            with progress_spinner("Creating instance..."):
                response = self.client.run_instances(
                    ImageId = ami_id,
                    InstanceType = instance_type_input,
                    KeyName = key_name,
                    SecurityGroupIds = [security_group_id],
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
        
        # Cleanup Security Groups
        print("Cleaning up associated Security Groups...")
        delete_security_groups()

    except Exception as e:
        console.print(f"[bold red]❌ Error during EC2 cleanup:[/bold red] {e}")
