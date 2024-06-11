import boto3
region='us-east-1'
aws_console = boto3.session.Session(profile_name="default",region_name=region)
ec2_console = aws_console.client(service_name="ec2")
result = ec2_console.describe_instances()['Reservations']

for ec2_instance in result:
    for value in ec2_instance['Instances']:
        print(value['InstanceId'])
