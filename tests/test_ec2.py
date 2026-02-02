import sys
import os

# 1. Add the parent folder to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Importing the class
from src.EC2.ec2_create_instance import EC2Creator
from src.EC2.change_instance_state import change_instance_state


def run_manual_tests():
    creator = EC2Creator()
    
    print("--- Starting Manual Testing from /tests folder ---")

    # AMI Check
    print("\nTesting AMI Resolution:")
    ubuntu_ami = creator.get_latest_ami_id("ubuntu")
    amazon_ami = creator.get_latest_ami_id("amazon-linux")
    
    if ubuntu_ami:
        print(f"✅ Ubuntu AMI: {ubuntu_ami}")
    if amazon_ami:
        print(f"✅ Amazon Linux AMI: {amazon_ami}")

    # בדיקת המכסה (Quota)
    print("\nTesting Quota Check:")
    if creator.is_quota_available():
        print("✅ Quota check passed.")
    else:
        print("⚠️  Quota reached or check failed.")

    # בדיקת יצירה (מושבת כברירת מחדל)
    print("\nTesting Instance Creation...")
    new_instance_id = creator.create_instance("amazon-linux", "t3.micro", "Nadav-Test-Instance")
    print(new_instance_id)

    print(f"\n🔄 Step 2: Testing instance STOP for {new_instance_id}")
    change_instance_state(new_instance_id, "stop")

    
    print("\n--- Testing Finished ---")

if __name__ == "__main__":
    run_manual_tests()