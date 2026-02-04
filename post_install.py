import pyfiglet
from rich.console import Console
from rich.panel import Panel
import time

def run_welcome():
    console = Console()
    
    title = pyfiglet.figlet_format("awsctl", font="starwars", justify="center")
    
    subtitle = "Made by Nadav Kamar | DevOps Engineer"
    
    console.print("\n")
    console.print(Panel(
        f"[bold cyan]{title}[/bold cyan]",
        border_style="blue",
        title="[bold green]Installation Complete![/bold green]",
        subtitle="[yellow]Platform Engineering Tool[/yellow]"
    ))
    
    console.print(f"[bold white]    >> ", end="")
    for char in subtitle:
        console.print(f"[bold white]{char}[/bold white]", end="")
        time.sleep(0.08)
    console.print("\n\n[bold]Ready to go! Type 'awsctl --help' to start.[/bold]\n")

if __name__ == "__main__":
    run_welcome()