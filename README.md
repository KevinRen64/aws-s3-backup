cat > README.md << 'EOF'
# S3 Backup CLI (boto3)

Python CLI tool to sync a local folder to an S3 bucket/prefix using boto3.
Designed for safe, repeatable backups and automation.

## Features
- Sync local directory to S3 (recursive)
- Upload only changed files (size+mtime metadata)
- Exclude patterns
- Dry-run mode (no changes)
- Optional delete (remove remote objects not present locally under the prefix)
- JSON output for pipelines

## Prerequisites
- Python 3.10+
- AWS credentials via `aws configure` (default profile) or IAM role
- S3 permissions: s3:ListBucket, s3:GetObject, s3:PutObject, (optional) s3:DeleteObject

## Install
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
