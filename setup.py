from setuptools import setup, find_packages
from setuptools.command.install import install
import subprocess
import sys


class PostInstallCommand(install):
    """Custom install command that shows the welcome banner after installation."""

    def run(self):
        # Run the standard install first
        install.run(self)

        # Now show the post-install banner
        try:
            subprocess.call([sys.executable, "post_install.py"])
        except Exception:
            pass


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
    },
)