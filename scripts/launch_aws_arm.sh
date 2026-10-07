#!/usr/bin/env bash
# One-shot ARM bench box (Graviton4, SVE2) once AWS account verification clears.
# Usage: scripts/launch_aws_arm.sh   (then bootstrap_remote.sh <ip> ~/.ssh/pleat-bench.pem arm-c8g)
set -euo pipefail
cd "$(dirname "$0")/.." && set -a && . ./.env && set +a
AMI=$(aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/arm64/hvm/ebs-gp3/ami-id --query Parameter.Value --output text)
SG=$(aws ec2 describe-security-groups --group-names pleat-bench-ssh --query 'SecurityGroups[0].GroupId' --output text)
ID=$(aws ec2 run-instances --image-id "$AMI" --instance-type c8g.2xlarge --key-name pleat-bench \
  --security-group-ids "$SG" --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=40,VolumeType=gp3}' \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=rcb-bench-arm},{Key=project,Value=pleated-ribbon-construction}]' \
  --query 'Instances[0].InstanceId' --output text)
echo "instance: $ID"
aws ec2 wait instance-running --instance-ids "$ID"
aws ec2 describe-instances --instance-ids "$ID" --query 'Reservations[0].Instances[0].PublicIpAddress' --output text
echo "REMEMBER: terminate when done — aws ec2 terminate-instances --instance-ids $ID (~\$0.29/h while up)"
