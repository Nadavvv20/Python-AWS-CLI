import boto3
from src.utils.helpers import console, get_aws_user, progress_spinner

current_user = get_aws_user()

def create_hosted_zones(domain_name):
    route53_client = boto3.client('route53')

    # Create the Hosted Zone
    try:
        response = route53_client.create_hosted_zone(
            Name=domain_name,
            CallerReference=str(hash(domain_name))
        )

        # Get the id
        zone_id = response['HostedZone']['Id']
        clean_zone_id = zone_id.split('/')[-1]
        console.print(f"[green]✅ Hosted Zone created for {domain_name} (ID: {clean_zone_id})[/green]")

        # Add tags
        route53_client.change_tags_for_resource(
                ResourceType='hostedzone',
                ResourceId=clean_zone_id,
                AddTags=[
                    {'Key': 'CreatedBy', 'Value': 'Nadav-Platform-CLI'},
                    {'Key': 'Owner', 'Value': current_user}
                ]
            )
        return clean_zone_id

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
        return None

def get_hosted_zones():
    """
    Returns a list of dictionaries with zone details (id, name, records) for platform zones.
    """
    r53 = boto3.client('route53')
    zones_response = r53.list_hosted_zones()
    
    platform_zones = []
    
    for zone in zones_response.get('HostedZones', []):
        zone_id = zone['Id'].split('/')[-1]
        
        # Check the tags for current zone
        try:
            tag_response = r53.list_tags_for_resource(
                ResourceType='hostedzone',
                ResourceId=zone_id
            )
            tags = {t['Key']: t['Value'] for t in tag_response['ResourceTagSet']['Tags']}
            
            if tags.get('CreatedBy') == 'Nadav-Platform-CLI':
                # Fetch records for this zone to return complete data
                records_response = r53.list_resource_record_sets(HostedZoneId=zone_id)
                records = records_response.get('ResourceRecordSets', [])
                
                platform_zones.append({
                    'Id': zone_id,
                    'Name': zone['Name'],
                    'Records': records
                })
        except Exception:
            # Skip if any error checking tags (e.g. permission issues)
            continue
            
    return platform_zones

def list_my_dns():
    try:
        with progress_spinner("Listing Hosted Zones..."):
            zones = get_hosted_zones()
            
            if not zones:
                console.print("[bold yellow]⚠️  No platform DNS zones found matching your criteria.[/bold yellow]")
                return

            for zone in zones:
                console.print(f"\n[bold cyan]📍 Hosted Zone: {zone['Name']} ({zone['Id']})[/bold cyan]")
                
                for record in zone['Records']:
                    if 'ResourceRecords' in record:
                        values = [r['Value'] for r in record['ResourceRecords']]
                        value_str = ", ".join(values)
                    elif 'AliasTarget' in record:
                        value_str = f"Alias -> {record['AliasTarget']['DNSName']}"
                    else:
                        value_str = "No Value"

                    console.print(f"  [yellow]•[/yellow] [bold]{record['Name']}[/bold] [cyan][{record['Type']}][/cyan] -> {value_str}")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")



def manage_dns_record(zone_id, action, record_name, record_type, value):
  
    route53_client = boto3.client('route53')
    
    clean_zone_id = zone_id.split('/')[-1]

    try:
        # 2Check the 
        tag_response = route53_client.list_tags_for_resource(
            ResourceType='hostedzone',
            ResourceId=clean_zone_id
        )
        
        tags = {t['Key']: t['Value'] for t in tag_response['ResourceTagSet']['Tags']}
        # Check the tag
        if tags.get('CreatedBy') != 'Nadav-Platform-CLI':
            console.print(f"[bold red]❌ Access Denied:[/bold red] Zone {clean_zone_id} is not managed by this CLI.")
            return False

        # Record Request 
        change_batch = {
            'Comment': f'Managed by Nadav-Platform-CLI',
            'Changes': [
                {
                    'Action': action.upper(),
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': record_type, 
                        'TTL': 300,
                        'ResourceRecords': [{'Value': value}]
                    }
                }
            ]
        }

        # Change in AWS
        response = route53_client.change_resource_record_sets(
            HostedZoneId=clean_zone_id,
            ChangeBatch=change_batch
        )
        
        console.print(f"[green]✅ DNS {action} successful for {record_name}![/green]")
        return True

    except Exception as e:
        console.print(f"[bold red]❌ Route53 Error:[/bold red] {e}")
        return False

def cleanup_dns_resources():
    r53 = boto3.client('route53')
    try:
        # 1. Get all the Hosted Zones
        zones_response = r53.list_hosted_zones()
        found_any = False
        
        from src.utils.helpers import progress_spinner
        
        with progress_spinner("Checking Route53 resources for cleanup..."):
            for zone in zones_response.get('HostedZones', []):
                zone_id = zone['Id'].split('/')[-1]
                
                # Check tags
                try:
                    tag_response = r53.list_tags_for_resource(
                        ResourceType='hostedzone',
                        ResourceId=zone_id
                    )
                    tags = {t['Key']: t['Value'] for t in tag_response['ResourceTagSet']['Tags']}
                    
                    if tags.get('CreatedBy') == 'Nadav-Platform-CLI':
                        found_any = True
                        console.print(f"  🗑️  Found platform zone: [cyan]{zone['Name']}[/cyan] ({zone_id})")
                        
                        # Delete records first
                        records = r53.list_resource_record_sets(HostedZoneId=zone_id)
                        changes = []
                        for record in records['ResourceRecordSets']:
                            if record['Type'] not in ['NS', 'SOA']:
                                changes.append({
                                    'Action': 'DELETE',
                                    'ResourceRecordSet': record
                                })
                        
                        if changes:
                             r53.change_resource_record_sets(
                                 HostedZoneId=zone_id,
                                 ChangeBatch={'Changes': changes}
                             )
                             console.print(f"     ✅ Deleted {len(changes)} records.")

                        # Delete zone
                        r53.delete_hosted_zone(Id=zone_id)
                        console.print(f"     ✅ Deleted Hosted Zone.")
                        
                except Exception as e:
                    console.print(f"  ❌ Error checking/deleting zone {zone_id}: {e}")

        if not found_any:
            console.print("[green]✨ No platform Route53 zones found to clean.[/green]")

    except Exception as e:
        console.print(f"[bold red]❌ Error during Route53 cleanup:[/bold red] {e}")
