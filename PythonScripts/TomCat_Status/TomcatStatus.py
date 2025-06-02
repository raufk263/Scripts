# SSM should be enabled to run this script.
# To perform POC - Launch EC2 instance and create SSM IAM role for SSMCoreinstance, attach the role to your ec2
# Make sure to allow port 22 in the security group.


import boto3
import time

ssm_client = boto3.client('ssm')
ec2_client = boto3.client('ec2')

def get_ssm_managed_instances():
    instances = []
    paginator = ssm_client.get_paginator('describe_instance_information')
    for page in paginator.paginate():
        for inst in page['InstanceInformationList']:
            instances.append(inst['InstanceId'])
    return instances

def get_instance_names(instance_ids):
    # Fetch tags for instances, get the Name tag for each
    names = {}
    if not instance_ids:
        return names

    reservations = ec2_client.describe_instances(InstanceIds=instance_ids)['Reservations']
    for reservation in reservations:
        for instance in reservation['Instances']:
            name = None
            if 'Tags' in instance:
                for tag in instance['Tags']:
                    if tag['Key'] == 'Name':
                        name = tag['Value']
                        break
            names[instance['InstanceId']] = name or "(No Name)"
    return names

def send_tomcat_check_command(instance_id):
    command = (
        'bash -c "'
        'if systemctl is-active --quiet tomcat; then systemctl status tomcat | grep Active; '
        'elif systemctl is-active --quiet tomcat8; then systemctl status tomcat8 | grep Active; '
        'elif systemctl is-active --quiet tomcat9; then systemctl status tomcat9 | grep Active; '
        'else echo Tomcat service not found or not running; fi"'
    )
    response = ssm_client.send_command(
        InstanceIds=[instance_id],
        DocumentName='AWS-RunShellScript',
        Parameters={'commands': [command]},
        Comment='Check Tomcat service status'
    )
    return response['Command']['CommandId']

def wait_for_command(instance_id, command_id, timeout=60):
    waited = 0
    while waited < timeout:
        response = ssm_client.list_command_invocations(
            CommandId=command_id,
            InstanceId=instance_id,
            Details=True
        )
        if not response['CommandInvocations']:
            time.sleep(2)
            waited += 2
            continue
        status = response['CommandInvocations'][0]['Status']
        if status in ('Success', 'Failed', 'Cancelled', 'TimedOut'):
            return status
        time.sleep(2)
        waited += 2
    return 'Timeout'

def get_command_output(instance_id, command_id):
    response = ssm_client.list_command_invocations(
        CommandId=command_id,
        InstanceId=instance_id,
        Details=True
    )
    if not response['CommandInvocations']:
        return None
    plugin = response['CommandInvocations'][0]['CommandPlugins'][0]
    return plugin.get('Output', '')

def main():
    print("🔍 Fetching SSM-managed EC2 instances...")
    instances = get_ssm_managed_instances()
    if not instances:
        print("⚠️ No SSM-managed instances found.")
        return
    print(f"✅ Found instances: {' '.join(instances)}")

    instance_names = get_instance_names(instances)

    for instance_id in instances:
        instance_name = instance_names.get(instance_id, "(No Name)")
        print("----------------------------------------------")
        print(f"📦 Instance ID: {instance_id} | Name: {instance_name}")

        try:
            command_id = send_tomcat_check_command(instance_id)
        except Exception as e:
            print(f"❌ Failed to send command to {instance_id}: {e}")
            continue

        print(f"🆔 Command ID: {command_id}")
        print("⏳ Waiting for command to complete...")

        status = wait_for_command(instance_id, command_id)
        if status != 'Success':
            print(f"⚠️ Command ended with status: {status}")
            continue

        output = get_command_output(instance_id, command_id)
        print("📋 Tomcat status output:")
        print(output or "(No output)")
        print("")

if __name__ == "__main__":
    main()
