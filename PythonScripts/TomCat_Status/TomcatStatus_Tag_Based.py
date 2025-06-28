import boto3
import time
import argparse

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
    info = {}
    if not instance_ids:
        return info

    reservations = ec2_client.describe_instances(InstanceIds=instance_ids)['Reservations']
    for reservation in reservations:
        for instance in reservation['Instances']:
            name = "(No Name)"
            for tag in instance.get('Tags', []):
                if tag['Key'] == 'Name':
                    name = tag['Value']
                    break
            info[instance['InstanceId']] = {'Name': name}
    return info


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
    parser = argparse.ArgumentParser(description='Check Tomcat on EC2 nodes.')
    valid_node_types = ['Application', 'Worker', 'all']

    parser.add_argument(
        '--type',
        required=True,
        help='Node type to filter: Application, Worker, or all (case-sensitive substring match on Name tag)'
    )

    args = parser.parse_args()
    node_type_filter = args.type

    if node_type_filter not in valid_node_types:
        parser.error(f"Invalid --type value '{args.type}'. Choose from: Application, Worker, all")

    print(f"🔍 Fetching SSM-managed EC2 instances...")
    ssm_managed_instances = get_ssm_managed_instances()

    print(f"🔍 Fetching all EC2 instances with Name filter: {node_type_filter}...")
    filters = [{'Name': 'instance-state-name', 'Values': ['running']}]
    if node_type_filter != 'all':
        filters.append({'Name': 'tag:Name', 'Values': [f"*{node_type_filter}*"]})

    reservations = ec2_client.describe_instances(Filters=filters)['Reservations']
    all_instance_ids = []
    for reservation in reservations:
        for instance in reservation['Instances']:
            all_instance_ids.append(instance['InstanceId'])

    instance_info = get_instance_names(all_instance_ids)

    if not instance_info:
        print(f"⚠️ No EC2 instances found matching Name filter '{node_type_filter}'.")
        return

    for instance_id, meta in instance_info.items():
        instance_name = meta['Name']
        print("\n----------------------------------------------")
        print(f"📦 Instance ID: {instance_id} | Name: {instance_name}")

        if instance_id in ssm_managed_instances:
            print("✅ SSM Agent is online")
        else:
            print("❌ SSM Agent is not online")
            print("🔌 Ping status: Connection lost")
            print("❗ The SSM Agent was unable to connect to a Systems Manager endpoint to register itself with the service.")
            continue

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
