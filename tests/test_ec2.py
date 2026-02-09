import sys
import os
import time

# 1. Add the parent folder to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Importing the class
from src.ec2.manager import EC2Creator, change_instance_state, cleanup_ec2_resources, list_instances
from src.utils.helpers import console

def run_integration_tests():
    creator = EC2Creator()
    console.print("[bold blue]--- Starting EC2 Integration Test ---[/bold blue]")

    try:
        # AMI Check
        console.print("\n[bold]1. Testing AMI Resolution:[/bold]")
        ubuntu_ami = creator.get_latest_ami_id("ubuntu")
        if ubuntu_ami:
            console.print(f"   ✅ Ubuntu AMI resolved: {ubuntu_ami}")
        else:
            raise Exception("Failed to resolve Ubuntu AMI")

        # Quota Check
        console.print("\n[bold]2. Testing Quota Check:[/bold]")
        if creator.is_quota_available():
            console.print("   ✅ Quota check passed.")
        else:
            console.print("   ⚠️  Quota reached (this might be expected if other instances exist).")

        # Create Instance
        console.print("\n[bold]3. Testing Instance Creation...[/bold]")
        instance_name = "Test-Auto-Instance"
        result_msg = creator.create_instance("amazon-linux", "t3.micro", instance_name, "test-key-auto")
        
        if not result_msg:
             raise Exception("Instance creation returned None.")
        
        # Extract ID (The function returns "Instance Id: i-xxxx")
        new_instance_id = result_msg.split(": ")[1].strip()
        console.print(f"   ✅ Instance Created: [cyan]{new_instance_id}[/cyan]")
        
        # List
        console.print("\n[bold]4. Testing List Instances...[/bold]")
        list_instances()

        # Stop Instance
        console.print(f"\n[bold]5. Testing Stop Instance {new_instance_id}...[/bold]")
        change_instance_state(new_instance_id, "stop")
        
        # Start Instance (Optional, but good to test)
        console.print(f"\n[bold]6. Testing Start Instance {new_instance_id}...[/bold]")
        change_instance_state(new_instance_id, "start")

        console.print("\n[bold green]✅ EC2 Flow Test Passed Successfully.[/bold green]")

    except Exception as e:
        console.print(f"\n[bold red]❌ Test Failed:[/bold red] {e}")
    finally:
        console.print("\n[bold]7. Cleanup Phase...[/bold]")
        cleanup_ec2_resources()

if __name__ == "__main__":
    run_integration_tests()