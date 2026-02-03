import boto3
from src.utils.ui_helper import console
from src.utils.aws_identity import get_aws_user
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


