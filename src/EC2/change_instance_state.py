import boto3
import os
import sys

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui_helpers import progress_spinner

# Accessing the EC2 service in us-east-1 region
# Accessing the EC2 service in us-east-1 region
ec2 = boto3.client('ec2', region_name='us-east-1')

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

if __name__ == "__main__":
    change_instance_state("i-02f2fd9e62ef03d8e", "stop")
