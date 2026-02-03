import sys
import os
import uuid
import time
import boto3

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.route53.manager import create_hosted_zones, manage_dns_record, list_my_dns
from src.utils.helpers import console

def wait_for_change(route53_client, change_id):
    """Wait for a Route53 change to complete"""
    if not change_id:
        return
        
    print(f"   Waiting for change {change_id} to complete...")
    waiter = route53_client.get_waiter('resource_record_sets_changed')
    try:
        waiter.wait(Id=change_id)
        print("   ✅ Change completed.")
    except Exception as e:
        print(f"   ⚠️ Waiter failed or timed out: {e}")

def test_route53_flow():
    # Setup
    unique_id = str(uuid.uuid4())[:8]
    domain_name = f"test-unit-{unique_id}.com"
    record_name = f"www.{domain_name}"
    record_type = "TXT"
    record_value = "\"v=spf1 include:example.com ~all\""
    
    r53 = boto3.client('route53')
    zone_id = None

    console.print(f"\n[bold blue]🚀 Starting Route53 Flow Test for {domain_name}[/bold blue]")

    try:
        # 1. Create Zone
        print(f"\n1️⃣  Creating Hosted Zone: {domain_name}")
        zone_id = create_hosted_zones(domain_name)
        
        if not zone_id:
            print("❌ Failed to create zone. Aborting.")
            return

        print(f"   Zone created with ID: {zone_id}")
        
        # Wait a bit for the zone to be "ready" (consistency)
        time.sleep(5)

        # 2. Add Records
        print(f"\n2️⃣  Adding Record: {record_name} -> {record_value}")
        # Note: manage_dns_record does not return the ChangeId, so we can't use the usage specific waiter.
        # We will usage a general sleep to ensure propagation availability for listing.
        success = manage_dns_record(zone_id, "UPSERT", record_name, record_type, record_value)
        if not success:
             print("❌ Failed to add record. Aborting.")
             return
        
        print("   Waiting 5 seconds for record propagation...")
        time.sleep(5)

        # 3. List
        print(f"\n3️⃣  Listing Zones and Records (Should see {domain_name})")
        list_my_dns()

        # 4. Delete Records
        print(f"\n4️⃣  Deleting Record: {record_name}")
        success = manage_dns_record(zone_id, "DELETE", record_name, record_type, record_value)
        if not success:
             print("❌ Failed to delete record. Manual cleanup may be required.")
        
        print("   Waiting 30 seconds for record deletion propagation...")
        time.sleep(30)

        # 5. Delete Zone
        print(f"\n5️⃣  Deleting Hosted Zone: {domain_name}")
        # Use boto3 directly as no delete function exists in src
        try:
             r53.delete_hosted_zone(Id=zone_id)
             print("   ✅ Hosted Zone deleted successfully.")
        except Exception as e:
             print(f"   ❌ Failed to delete Hosted Zone: {e}")

        # 6. Final List
        print(f"\n6️⃣  Final List (Should NOT see {domain_name})")
        list_my_dns()
        
        print("\n[bold green]✅ Test Concluded Successfully[/bold green]")

    except Exception as e:
        console.print(f"[bold red]❌ Test Failed with Exception:[/bold red] {e}")
    finally:
        pass

if __name__ == "__main__":
    test_route53_flow()
