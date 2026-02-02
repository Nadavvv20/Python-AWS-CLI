import sys
import os

# 1. Add the parent folder to the path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 2. Importing the class
from src.EC2.ec2_create_instance import EC2Manager

def run_manual_tests():
    manager = EC2Manager()
    
    print("--- Starting Manual Testing from /tests folder ---")

    # AMI Check
    print("\nTesting AMI Resolution:")
    ubuntu_ami = manager.get_latest_ami_id("ubuntu")
    amazon_ami = manager.get_latest_ami_id("amazon-linux")
    
    if ubuntu_ami:
        print(f"✅ Ubuntu AMI: {ubuntu_ami}")
    if amazon_ami:
        print(f"✅ Amazon Linux AMI: {amazon_ami}")

    # בדיקת המכסה (Quota)
    print("\nTesting Quota Check:")
    if manager.is_quota_available():
        print("✅ Quota check passed.")
    else:
        print("⚠️  Quota reached or check failed.")

    # בדיקת יצירה (מושבת כברירת מחדל)
    print("\nTesting Instance Creation...")
    return_message = manager.create_instance("amazon-linux", "t3.micro", "Nadav-Test-Instance")
    print(return_message)

    print("\n--- Testing Finished ---")

if __name__ == "__main__":
    run_manual_tests()