# DevOps Automation Scripts

A collection of Python automation scripts using **boto3** (AWS SDK) and **paramiko** (SSH/SFTP) for common DevOps tasks.

---

## Script Overview

### AWS (boto3) Scripts
| File | Description |
|------|--------------|
| `ec2_start_stop.py` | Start or stop EC2 instances based on tag filters. |
| `s3_upload_lifecycle.py` | Upload a local directory to S3 with encryption and lifecycle policy. |
| `rds_snapshot_prune.py` | Create on-demand RDS snapshots and prune older ones. |
| `cloudwatch_alarm_cpu.py` | Create a CloudWatch CPU alarm for an EC2 instance with SNS notification. |

---

### SSH (paramiko) Scripts
| File | Description |
|------|--------------|
| `parallel_ssh.py` | Run a shell command across multiple hosts concurrently over SSH. |

---

## AWS Credentials Setup

To allow the boto3 scripts to authenticate with AWS, configure your credentials locally.

1. **Create the AWS config directory (if not exists):**
   ```bash
   mkdir -p ~/.aws
   ```

2. **Add your credentials in ~/.aws/credentials:**
   ```bash
   [default]
   aws_access_key_id = YOUR_AWS_ACCESS_KEY_ID
   aws_secret_access_key = YOUR_AWS_SECRET_ACCESS_KEY
   ```
3. **Verify your configuration:**
   ```bash
   aws sts get-caller-identity
   ```

## Requirements
  Install dependencies
  
**Verify your configuration:**
   ```bash
   aws sts get-caller-identity
   ```
