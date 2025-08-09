🧾 Overview
This project is an AWS Lambda function that monitors the following resources daily:

EC2 Instances

RDS Instances

ECS Services

EBS Volumes

Elastic IPs

It checks usage and cost-impacting resources, composes a detailed report, and sends it via Amazon SNS to a subscribed email address. The email subject line includes the current date (e.g., 8 August, 2025).

Features
Daily scheduled Lambda execution

Resource checks with Free Tier cost warnings

Clean, readable email summary

Human-readable date format in subject line

Configurable via EventBridge (CloudWatch Events)


Start (Scheduled Trigger via EventBridge)
         │
         ▼
[1] Lambda Function Starts
         │
         ▼
[2] Analyze AWS Resources
     └─> Collect data from EC2, RDS, ECS, EBS, Elastic IPs
     └─> Prepare usage and cost insights
         │
         ▼
[3] Compose Final Report
     └─> Build email message content
     └─> Format current date (e.g., "8 August, 2025")
         │
         ▼
[4] Send Email via SNS
     └─> Use sns.publish() with subject line and report
         │
         ▼
End (Lambda returns statusCode and report body)



