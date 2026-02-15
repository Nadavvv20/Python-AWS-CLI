import sys
from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop


def _post_install_banner():
    """Display the welcome banner after installation."""
    try:
        from rich.console import Console
        from rich.panel import Panel
        import pyfiglet
        import time

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
    except Exception:
        pass


class PostInstallCommand(install):
    """Custom install command - shows welcome banner after install."""
    def run(self):
        install.run(self)
        _post_install_banner()


class PostDevelopCommand(develop):
    """Custom develop command - shows welcome banner after editable install."""
    def run(self):
        develop.run(self)
        _post_install_banner()


setup(
    name="awsctl",
    version="0.1.1",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "click",
        "rich",
        "pyfiglet",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "awsctl = src.cli:main_cli",
        ],
    },
    cmdclass={
        "install": PostInstallCommand,
        "develop": PostDevelopCommand,
    },
)


)
