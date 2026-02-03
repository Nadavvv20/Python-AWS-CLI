import boto3
import os
import sys
# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ui_helper import progress_spinner
from rich.console import Console
console = Console()

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


    