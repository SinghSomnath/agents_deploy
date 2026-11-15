# AWS Secrets Manager Integration Guide

This guide explains how to configure the LangGraph PDF WebCrawl Router Agent to fetch environment variables from AWS Secrets Manager instead of using a local `.env` file.

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Setup AWS Secrets Manager](#setup-aws-secrets-manager)
- [Configure the Application](#configure-the-application)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)

## 🌟 Overview

The application now supports loading secrets from AWS Secrets Manager, providing:

- **✅ Centralized secret management** - Single source of truth for all environments
- **✅ Enhanced security** - No sensitive data in `.env` files or code
- **✅ Easy rotation** - Update secrets in AWS without redeploying
- **✅ Audit logging** - Track secret access via AWS CloudTrail
- **✅ Fallback support** - Automatically falls back to `.env` file if AWS is unavailable

## 🔧 Prerequisites

### 1. Install boto3

```bash
pip install boto3

# Or install all dependencies
pip install -r requirements.txt
```

### 2. AWS Account & IAM Permissions

You need an AWS account with permissions to:
- Create and access AWS Secrets Manager secrets
- (Optional) IAM role for EC2/ECS if running on AWS infrastructure

## 🔐 Setup AWS Secrets Manager

### Step 1: Create a Secret in AWS Console

1. Go to [AWS Secrets Manager Console](https://console.aws.amazon.com/secretsmanager/)
2. Click **"Store a new secret"**
3. Select **"Other type of secret"**
4. Choose **"Plaintext"** and paste your configuration as JSON:

```json
{
  "OPENROUTER_API_KEY": "sk-or-v1-your-openrouter-key",
  "OPENROUTER_MODEL": "qwen/qwen3-embedding-8b",
  "OPENROUTER_MODEL_DIMENSIONS": "4096",
  "ASTRA_DB_API_ENDPOINT": "https://your-database-id.apps.astra.datastax.com",
  "ASTRA_DB_APPLICATION_TOKEN": "AstraCS:your-token",
  "ASTRA_DB_COLLECTION": "langgraph_collection",
  "ASTRA_DB_KEYSPACE": "default_keyspace",
  "LANGCHAIN_API_KEY": "lsv2_pt_your-langchain-key",
  "LANGCHAIN_PROJECT": "GenAIAPPWithOPENAI"
}
```

5. Click **"Next"**
6. Enter a **Secret name** (e.g., `langgraph-agent-secrets-prod`)
7. (Optional) Add description and tags
8. Click **"Next"** → **"Next"** → **"Store"**

### Step 2: Create via AWS CLI (Alternative)

```bash
# Create secret from JSON file
aws secretsmanager create-secret \
    --name langgraph-agent-secrets-prod \
    --description "Production secrets for LangGraph PDF WebCrawl Router Agent" \
    --secret-string file://secrets.json \
    --region us-east-1

# Or create directly
aws secretsmanager create-secret \
    --name langgraph-agent-secrets-prod \
    --secret-string '{
      "OPENROUTER_API_KEY": "sk-or-v1-...",
      "ASTRA_DB_API_ENDPOINT": "https://...",
      "ASTRA_DB_APPLICATION_TOKEN": "AstraCS:..."
    }' \
    --region us-east-1
```

### Step 3: Grant Access (IAM Policy)

Create an IAM policy with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:langgraph-agent-secrets-prod-*"
    }
  ]
}
```

Attach this policy to:
- **EC2 Instance Role** (if running on EC2)
- **ECS Task Role** (if running on ECS/Fargate)
- **Lambda Execution Role** (if running on Lambda)
- **IAM User** (for local development)

## ⚙️ Configure the Application

### Option 1: Using Environment Variables

Set these environment variables:

```bash
# Enable AWS Secrets Manager
export USE_AWS_SECRETS=true

# AWS Secret configuration
export AWS_SECRET_NAME=langgraph-agent-secrets-prod
export AWS_REGION=us-east-1

# AWS Credentials (if not using IAM role)
export AWS_ACCESS_KEY_ID=AKIA...
export AWS_SECRET_ACCESS_KEY=...
```

### Option 2: Update .env File

Add to your `.env` file:

```bash
# AWS Secrets Manager Configuration
USE_AWS_SECRETS=true
AWS_SECRET_NAME=langgraph-agent-secrets-prod
AWS_REGION=us-east-1

# AWS Credentials (only if not using IAM role)
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=...
```

**Note:** When `USE_AWS_SECRETS=true`, the application will:
1. Try to fetch secrets from AWS Secrets Manager
2. Fall back to `.env` file if AWS is unavailable
3. Override any `.env` values with AWS secrets

## 💻 Local Development

### Approach 1: Use .env File (Recommended for Local Dev)

```bash
# .env
USE_AWS_SECRETS=false  # Disable AWS Secrets Manager
OPENROUTER_API_KEY=sk-or-v1-...
ASTRA_DB_API_ENDPOINT=https://...
# ... other variables
```

Run normally:
```bash
python langgraph_pdf_webcrawl_router_agent.py
```

### Approach 2: Use AWS with Local Credentials

```bash
# .env
USE_AWS_SECRETS=true
AWS_SECRET_NAME=langgraph-agent-secrets-dev
AWS_REGION=us-east-1

# Configure AWS credentials
aws configure
# Enter: Access Key ID, Secret Access Key, Region

# Run application
python langgraph_pdf_webcrawl_router_agent.py
```

## 🚀 Production Deployment

### EC2 / ECS / Fargate

1. **Attach IAM Role** with Secrets Manager permissions
2. **Set environment variables**:
   ```bash
   USE_AWS_SECRETS=true
   AWS_SECRET_NAME=langgraph-agent-secrets-prod
   AWS_REGION=us-east-1
   ```
3. **No AWS credentials needed** - IAM role provides automatic authentication

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Set AWS Secrets Manager config
ENV USE_AWS_SECRETS=true
ENV AWS_SECRET_NAME=langgraph-agent-secrets-prod
ENV AWS_REGION=us-east-1

CMD ["uvicorn", "langgraph_pdf_webcrawl_router_agent:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Run with AWS credentials:**
```bash
docker run -p 8000:8000 \
  -e AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY_ID \
  -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET_ACCESS_KEY \
  langgraph-agent:latest
```

**Or mount AWS credentials:**
```bash
docker run -p 8000:8000 \
  -v ~/.aws:/root/.aws:ro \
  langgraph-agent:latest
```

### Kubernetes Deployment

```yaml
apiVersion: v1
kind: Deployment
metadata:
  name: langgraph-agent
spec:
  replicas: 2
  template:
    spec:
      serviceAccountName: langgraph-agent-sa  # With IAM role (IRSA)
      containers:
      - name: agent
        image: langgraph-agent:latest
        env:
        - name: USE_AWS_SECRETS
          value: "true"
        - name: AWS_SECRET_NAME
          value: "langgraph-agent-secrets-prod"
        - name: AWS_REGION
          value: "us-east-1"
```

## 🐛 Troubleshooting

### Issue 1: "boto3 not installed"

**Solution:**
```bash
pip install boto3
```

### Issue 2: "AWS credentials not found"

**Symptoms:**
```
⚠️  AWS credentials not found. Falling back to .env file.
```

**Solutions:**
1. **For IAM Role (EC2/ECS):** Ensure the IAM role is properly attached
2. **For local development:**
   ```bash
   aws configure
   # Or export credentials
   export AWS_ACCESS_KEY_ID=AKIA...
   export AWS_SECRET_ACCESS_KEY=...
   ```
3. **Verify credentials:**
   ```bash
   aws sts get-caller-identity
   ```

### Issue 3: "Secret not found"

**Symptoms:**
```
❌ Secret 'my-secret' not found in AWS Secrets Manager
```

**Solutions:**
1. Verify secret name:
   ```bash
   aws secretsmanager list-secrets --region us-east-1
   ```
2. Check region matches:
   ```bash
   echo $AWS_REGION
   ```
3. Verify permissions:
   ```bash
   aws secretsmanager get-secret-value --secret-id langgraph-agent-secrets-prod
   ```

### Issue 4: "Access Denied"

**Symptoms:**
```
❌ Error fetching secret from AWS: An error occurred (AccessDeniedException)
```

**Solutions:**
1. **Check IAM permissions** - Ensure `secretsmanager:GetSecretValue` is granted
2. **Verify resource ARN** in IAM policy matches your secret
3. **Test manually:**
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id langgraph-agent-secrets-prod \
     --region us-east-1
   ```

### Issue 5: "Invalid JSON in secret"

**Symptoms:**
```
❌ Failed to parse secret as JSON
```

**Solutions:**
1. Verify JSON syntax:
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id langgraph-agent-secrets-prod \
     --query SecretString \
     --output text | jq .
   ```
2. Update secret with valid JSON:
   ```bash
   aws secretsmanager update-secret \
     --secret-id langgraph-agent-secrets-prod \
     --secret-string file://secrets.json
   ```

### Testing AWS Integration

Test the AWS Secrets Manager integration:

```bash
python aws_secrets.py
```

Expected output:
```
Testing AWS Secrets Manager integration...

🔧 Initializing environment configuration...
🔐 Fetching secret 'langgraph-agent-secrets-prod' from AWS Secrets Manager (region: us-east-1)
✅ Successfully fetched 8 secrets from AWS Secrets Manager
✅ Loaded 8 secrets from AWS Secrets Manager
✅ Environment initialization complete

📋 Configuration Summary:
  USE_AWS_SECRETS: true
  AWS_SECRET_NAME: langgraph-agent-secrets-prod
  AWS_REGION: us-east-1
  OPENROUTER_API_KEY: ✓ set
  ASTRA_DB_API_ENDPOINT: ✓ set
  ASTRA_DB_APPLICATION_TOKEN: ✓ set
```

## 🔄 Secret Rotation

To update secrets without redeploying:

```bash
# Update secret value
aws secretsmanager update-secret \
  --secret-id langgraph-agent-secrets-prod \
  --secret-string '{
    "OPENROUTER_API_KEY": "sk-or-v1-NEW-KEY",
    "ASTRA_DB_API_ENDPOINT": "https://..."
  }'

# Restart application to pick up new values
# The application fetches secrets on startup
```

## 📊 Monitoring

Monitor secret access via AWS CloudTrail:

1. Go to [CloudTrail Console](https://console.aws.amazon.com/cloudtrail/)
2. Look for `GetSecretValue` events
3. Filter by secret name: `langgraph-agent-secrets-prod`

## 🔒 Security Best Practices

1. **Use IAM Roles** instead of access keys whenever possible
2. **Principle of Least Privilege** - Grant only `GetSecretValue` permission
3. **Separate secrets** by environment (dev, staging, prod)
4. **Enable secret rotation** for long-lived credentials
5. **Use VPC endpoints** for Secrets Manager in private subnets
6. **Enable CloudTrail logging** to audit secret access
7. **Never commit** `.env` files with real credentials
8. **Use resource policies** to restrict secret access

## 📚 Additional Resources

- [AWS Secrets Manager Documentation](https://docs.aws.amazon.com/secretsmanager/)
- [boto3 Secrets Manager Reference](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html)
- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

---

**Need Help?** Check the [Troubleshooting](#troubleshooting) section or open an issue on GitHub.
