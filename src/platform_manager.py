from rich.table import Table
from src.utils.helpers import console, progress_spinner
from src.ec2.manager import get_instances, cleanup_ec2_resources
from src.s3.manager import get_buckets, cleanup_s3_resources
from src.route53.manager import get_hosted_zones, cleanup_dns_resources

def list_all_resources():
    """
    Lists all resources (EC2, S3, Route53) created by the platform in a table.
    """
    table = Table(title="☁️  Platform Resources Overview", show_header=True, header_style="bold magenta")
    
    table.add_column("Type", style="cyan", width=12)
    table.add_column("Resource Name / ID", style="bold white")
    table.add_column("Status / Details", style="yellow")
    table.add_column("Additional Info", style="dim")

    has_resources = False

    try:
        with progress_spinner("Gathering all platform resources..."):
            # 1. EC2 Instances
            instances = get_instances()
            for inst in instances:
                has_resources = True
                name_tag = next((tag['Value'] for tag in inst.get('Tags', []) if tag['Key'] == 'Name'), "N/A")
                state = inst['State']['Name']
                state_color = "green" if state == "running" else "red" if state in ["stopped", "terminated"] else "yellow"
                
                table.add_row(
                    "EC2 Instance", 
                    f"{name_tag}\n({inst['InstanceId']})", 
                    f"[{state_color}]{state.upper()}[/{state_color}]", 
                    f"Type: {inst['InstanceType']}\nIP: {inst.get('PublicIpAddress', 'N/A')}"
                )

            # 2. S3 Buckets
            buckets = get_buckets()
            for bucket in buckets:
                has_resources = True
                table.add_row(
                    "S3 Bucket", 
                    bucket, 
                    "[green]ACTIVE[/green]", 
                    "Region: us-east-1" # Assuming us-east-1 as it's the default, fetching logic could be improved if needed
                )

            # 3. Route53 Zones
            zones = get_hosted_zones()
            for zone in zones:
                has_resources = True
                record_count = len(zone['Records'])
                table.add_row(
                    "DNS Zone", 
                    f"{zone['Name']}\n({zone['Id']})", 
                    "[green]ACTIVE[/green]", 
                    f"{record_count} Records"
                )

        if has_resources:
            console.print(table)
        else:
            console.print("\n[bold yellow]✨ No platform resources found.[/bold yellow]")

    except Exception as e:
        console.print(f"[bold red]❌ Error listing all resources:[/bold red] {e}")


def cleanup_all_resources():
    """
    Cleans up ALL resources created by the platform.
    """
    console.print("[bold red]⚠️  WARNING: This will DESTROY ALL resources created by this CLI tool![/bold red]")
    confirm = input("Are you SURE you want to proceed? Type 'delete-all' to confirm: ")
    
    if confirm != "delete-all":
        console.print("[yellow]🛑 Cleanup cancelled.[/yellow]")
        return

    console.print("\n[bold red]🚀 Starting Global Cleanup...[/bold red]")
    
    try:
        # 1. Clean EC2
        console.print("\n[bold cyan]--- Cleaning EC2 Resources ---[/bold cyan]")
        cleanup_ec2_resources()
        
        # 2. Clean S3
        console.print("\n[bold cyan]--- Cleaning S3 Resources ---[/bold cyan]")
        cleanup_s3_resources()
        
        # 3. Clean Route53
        console.print("\n[bold cyan]--- Cleaning Route53 Resources ---[/bold cyan]")
        cleanup_dns_resources()
        
        console.print("\n[bold green]✨ Global Cleanup Complete! ✨[/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Error during global cleanup:[/bold red] {e}")
