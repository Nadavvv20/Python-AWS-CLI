import boto3
from src.utils.ui_helper import console
from src.utils.aws_identity import get_aws_user
current_user = get_aws_user()

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
        # בדיקה אם הטאג קיים והערך שלו מתחיל ב-Nadav-Platform-CLI
        if tags.get('CreatedBy') != 'Nadav-Platform-CLI':
            console.print(f"[bold red]❌ Access Denied:[/bold red] Zone {clean_zone_id} is not managed by this CLI.")
            return False

        # 3. בניית הבקשה לשינוי הרקורד
        change_batch = {
            'Comment': f'Managed by Nadav-Platform-CLI',
            'Changes': [
                {
                    'Action': action.upper(), # UPSERT או DELETE
                    'ResourceRecordSet': {
                        'Name': record_name,
                        'Type': record_type, # למשל 'A', 'CNAME', 'TXT'
                        'TTL': 300,
                        'ResourceRecords': [{'Value': value}]
                    }
                }
            ]
        }

        # 4. ביצוע השינוי ב-AWS
        response = route53_client.change_resource_record_sets(
            HostedZoneId=clean_zone_id,
            ChangeBatch=change_batch
        )
        
        console.print(f"[green]✅ DNS {action} successful for {record_name}![/green]")
        return True

    except Exception as e:
        console.print(f"[bold red]❌ Route53 Error:[/bold red] {e}")
        return False