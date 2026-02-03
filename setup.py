from setuptools import setup, find_packages

setup(
    name='awsctl',
    version='0.1.0',
    packages=find_packages(),
    py_modules=['main'],
    include_package_data=True,
    install_requires=[
        'click',
        'boto3',
        'rich',
    ],
    entry_points={
        'console_scripts': [
            'awsctl = main:cli', 
        ],
    },
)