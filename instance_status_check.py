import os
import boto3
import requests
from datetime import datetime

bot_token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('TELEGRAM_CHAT_ID')

if not bot_token or not chat_id:
    print("Error: Telegram credentials are missing!")
    exit(1)

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

# 1. Connect to AWS, and get the relevant instances info into "respone" dictionary
ec2 = boto3.client('ec2', region_name='us-east-1')
response = ec2.describe_instances(
    Filters=[
    {'Name': 'instance-state-name', 'Values': ['running']},
    {'Name': 'tag:CreatedBy', 'Values': ['Nadav-Platform-CLI']}
    ]
)

server_count = 0
for reservation in response['Reservations']:
    server_count += len(reservation['Instances'])

# 2. Create the message
if server_count > 0:
    message = f"🤖 Jenkins Report:\nDate: {datetime.now()}\nPipeline finished successfully!\n\
Currently, there are {server_count} active servers made by the platform in AWS.\n\
Don't forget to shut them down to save costs, by running 'awsctl ec2 cleanup'." 
else:
    message = f"🤖 Jenkins Report:\nDate: {datetime.now()}\nPipeline finished successfully!\n\
Currently, there are {server_count} active servers made by the platform.\n\
You can stay calm 😌"


# 3. Send to Telegram
payload = {
    "chat_id": chat_id,
    "text": message
}

requests.post(url, json=payload)
