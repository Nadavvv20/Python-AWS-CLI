from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
import subprocess
import sys

def show_banner():
    """Runs welcome script"""
    try:

        subprocess.check_call([sys.executable, "post_install.py"])
    except Exception:
        pass 

class PostDevelopCommand(develop):
    """ Runs after 'pip install -e .' """
    def run(self):
        develop.run(self)
        show_banner()

setup(
    name="awsctl",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "click",
        "rich",
        "pyfiglet"
    ],
    entry_points={
        "console_scripts": [
            "awsctl = src.cli:main_cli",
        ],
    },
    cmdclass={
        'develop': PostDevelopCommand, # מפעיל את הבאנר בהתקנה במצב פיתוח
    },
)