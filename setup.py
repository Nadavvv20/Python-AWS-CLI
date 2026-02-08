from setuptools import setup, find_packages

setup(
    name="awsctl",
    version="0.1.1",
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
)