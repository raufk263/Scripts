import boto3
from datetime import datetime

def lambda_handler(event, context):
    ec2 = boto3.client('ec2')
    rds = boto3.client('rds')
    ecs = boto3.client('ecs')
    sns = boto3.client('sns')

    message_lines = []

    # -----------------------------
    # Check EC2 Running Instances
    # -----------------------------
    ec2_response = ec2.describe_instances(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    running_ec2 = []
    for reservation in ec2_response['Reservations']:
        for instance in reservation['Instances']:
            running_ec2.append(instance['InstanceId'])

    if running_ec2:
        message_lines.append(f"🔶 Running EC2 Instances:\n - " + "\n - ".join(running_ec2))
    else:
        message_lines.append("✅ No EC2 instances are running.")

    # -----------------------------
    # Check RDS Instances
    # -----------------------------
    rds_response = rds.describe_db_instances()
    running_rds = [db['DBInstanceIdentifier'] for db in rds_response['DBInstances'] if db['DBInstanceStatus'] == 'available']

    if running_rds:
        message_lines.append(f"\n🔶 Running RDS Instances:\n - " + "\n - ".join(running_rds))
    else:
        message_lines.append("\n✅ No RDS instances are running.")

    # -----------------------------
    # Check ECS Running Services
    # -----------------------------
    ecs_clusters = ecs.list_clusters()['clusterArns']
    running_ecs_services = []

    for cluster_arn in ecs_clusters:
        services = ecs.list_services(cluster=cluster_arn)['serviceArns']
        if services:
            described = ecs.describe_services(cluster=cluster_arn, services=services)['services']
            for svc in described:
                if svc['runningCount'] > 0:
                    running_ecs_services.append(f"{svc['serviceName']} in {cluster_arn}")

    if running_ecs_services:
        message_lines.append(f"\n🔶 Running ECS Services:\n - " + "\n - ".join(running_ecs_services))
    else:
        message_lines.append("\n✅ No ECS services are running.")

    # -----------------------------
    # Check EBS Volumes
    # -----------------------------
    ebs_response = ec2.describe_volumes()
    all_volumes = ebs_response['Volumes']
    
    unattached_ebs = [vol['VolumeId'] for vol in all_volumes if vol['State'] == 'available']
    total_ebs_gb = sum(vol['Size'] for vol in all_volumes)  # Size is in GiB

    if unattached_ebs:
        message_lines.append(f"\n⚠️ Unattached EBS Volumes (incur cost):\n - " + "\n - ".join(unattached_ebs))
        message_lines.append("💡 Note: Unattached volumes are not covered by the Free Tier and WILL incur charges.")
    else:
        message_lines.append("\n✅ No unattached EBS volumes found.")

    message_lines.append(f"\n📦 Total EBS Volume Usage: {total_ebs_gb} GiB")
    if total_ebs_gb > 30:
        message_lines.append("❌ EBS usage exceeds the 30 GiB Free Tier limit. Charges will apply.")
    else:
        message_lines.append("✅ EBS usage is within the 30 GiB Free Tier limit.")

    # -----------------------------
    # Check Unassociated Elastic IPs
    # -----------------------------
    addresses = ec2.describe_addresses()
    unused_ips = [addr['PublicIp'] for addr in addresses['Addresses'] if 'InstanceId' not in addr]

    if unused_ips:
        message_lines.append(f"\n⚠️ Unassociated Elastic IPs (incur cost):\n - " + "\n - ".join(unused_ips))
        message_lines.append("💡 Note: Elastic IPs are free **only when attached to a running instance**. These WILL incur hourly charges.")
    else:
        message_lines.append("\n✅ No unused Elastic IPs found.")

    # -----------------------------
    # Send the Final Summary Email
    # -----------------------------
    final_message = "\n".join(message_lines)

    # Format date as "8 August, 2025"
    today = datetime.utcnow().strftime("%-d %B, %Y")  # For AWS Lambda (Amazon Linux)

    subject_line = f"[AWS Alert] Daily Resource Usage Summary - {today}"

    sns.publish(
        TopicArn='arn:aws:sns:us-west-2:798278983508:daily-resource-alerts',
        Subject=subject_line,
        Message=final_message
    )

    return {
        'statusCode': 200,
        'body': final_message
    }
