import boto3
from src.utils.ui_helper import console

def list_my_dns():
    r53 = boto3.client('route53')
    
    try:
        # 1. Get all the Hosted Zones
        zones_response = r53.list_hosted_zones()
        
        for zone in zones_response.get('HostedZones', []):
            zone_id = zone['Id'].split('/')[-1]
            
            # Check the tags for current zone
            tag_response = r53.list_tags_for_resource(
                ResourceType='hostedzone',
                ResourceId=zone_id
            )
            
            tags = {t['Key']: t['Value'] for t in tag_response['ResourceTagSet']['Tags']}
            
            # Condition only if the tag is correct
            if tags.get('CreatedBy') == 'Nadav-Platform-CLI':
                console.print(f"\n[bold cyan]📍 Hosted Zone: {zone['Name']} ({zone_id})[/bold cyan]")
                
                # List the records of the current zone
                records = r53.list_resource_record_sets(HostedZoneId=zone_id)
                
                for record in records.get('ResourceRecordSets', []):
                    if 'ResourceRecords' in record:
                        values = [r['Value'] for r in record['ResourceRecords']]
                        value_str = ", ".join(values)
                    elif 'AliasTarget' in record:
                        value_str = f"Alias -> {record['AliasTarget']['DNSName']}"
                    else:
                        value_str = "No Value"

                    console.print(f"  [yellow]•[/yellow] [bold]{record['Name']}[/bold] [{record['Type']}] -> {value_str}")

    except Exception as e:
        console.print(f"[bold red]❌ Error:[/bold red] {e}")
