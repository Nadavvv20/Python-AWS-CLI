import boto3

def get_aws_user():
    # Get the name of the current AWS user
    sts = boto3.client('sts')
    try:
        identity = sts.get_caller_identity()
        return identity['Arn'].split('/')[-1]
    except Exception:
        return "Unknown-User"