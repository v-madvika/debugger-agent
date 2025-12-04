# AWS Bedrock Setup Guide

## 🎯 Quick Setup for AWS Bedrock

The system is now configured to use AWS Bedrock instead of Anthropic API.

## ✅ Step 1: Enable Bedrock Model Access

1. **Log in to AWS Console**: https://console.aws.amazon.com/
2. **Navigate to Bedrock**:
   - Search for "Bedrock" in the top search bar
   - Click on "Amazon Bedrock"
3. **Enable Model Access**:
   - Click "Model access" in the left sidebar
   - Click "Enable specific models" or "Modify model access"
   - Find **Anthropic → Claude 3.5 Sonnet v2**
   - Check the box next to: `anthropic.claude-3-5-sonnet-20241022-v2:0`
   - Click "Request model access" or "Save changes"
   - Wait for approval (usually instant)

## ✅ Step 2: Create IAM User for API Access

1. **Go to IAM Console**: https://console.aws.amazon.com/iam/
2. **Create User**:
   - Click "Users" → "Create user"
   - User name: `bedrock-agent` (or any name)
   - Click "Next"
3. **Set Permissions**:
   - Select "Attach policies directly"
   - Search and select: **`AmazonBedrockFullAccess`**
   - Click "Next" → "Create user"
4. **Create Access Key**:
   - Click on the newly created user
   - Go to "Security credentials" tab
   - Click "Create access key"
   - Select "Application running outside AWS"
   - Click "Next" → "Create access key"
   - **IMPORTANT**: Copy both:
     - Access key ID (starts with `AKIA...`)
     - Secret access key (long string - only shown once!)

## ✅ Step 3: Update .env File

Edit your `.env` file with AWS credentials:

```env
# AWS Bedrock Configuration
USE_BEDROCK=true
AWS_ACCESS_KEY_ID=AKIA...your-access-key...
AWS_SECRET_ACCESS_KEY=your-secret-access-key...
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0

# JIRA Configuration (keep these as before)
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=ATATT...
JIRA_PROJECT_KEY=KAN

# Browser Settings
HEADLESS_BROWSER=false
AUTO_POST_TO_JIRA=false
```

## ✅ Step 4: Verify Setup

```bash
cd agent
python setup_check.py
```

You should see:
- ✓ Environment File
- ✓ Package Installation
- ✓ JIRA Connection
- ✓ AWS Bedrock (instead of Anthropic API)
- ✓ Playwright Browser

## ✅ Step 5: Run the Agent

```bash
python bug_reproduction_agent.py KAN-4
```

You should see:
```
✓ Using AWS Bedrock for AI
✓ JIRA Client initialized
```

## 🌍 Available AWS Regions

Bedrock is available in these regions (choose the closest one):

- `us-east-1` - US East (N. Virginia) - **Recommended**
- `us-west-2` - US West (Oregon)
- `ap-southeast-1` - Asia Pacific (Singapore)
- `ap-northeast-1` - Asia Pacific (Tokyo)
- `eu-central-1` - Europe (Frankfurt)
- `eu-west-3` - Europe (Paris)

Update `AWS_REGION` in `.env` if needed.

## 💰 Pricing

**Claude 3.5 Sonnet v2 on Bedrock:**
- Input: ~$3 per million tokens
- Output: ~$15 per million tokens

**Typical bug reproduction:**
- Uses ~10,000-20,000 tokens per run
- Cost: ~$0.10-$0.30 per bug

## 🔒 Security Best Practices

1. **Never commit** `.env` file to git
2. **Use IAM roles** instead of access keys when possible
3. **Rotate access keys** regularly
4. **Set up CloudWatch** billing alerts
5. **Use least-privilege** IAM policies

## 🆚 Bedrock vs Anthropic API

| Feature | AWS Bedrock | Anthropic API |
|---------|-------------|---------------|
| Setup | More complex | Simple |
| Billing | AWS account | Credit card |
| Security | AWS IAM | API key |
| Compliance | AWS certified | Standard |
| Pricing | Slightly lower | Standard |
| Best for | Enterprise | Individual |

## 🐛 Troubleshooting

### Error: "Model access not granted"
- Go to Bedrock console → Model access
- Enable Claude 3.5 Sonnet v2
- Wait 1-2 minutes for propagation

### Error: "Invalid credentials"
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
- Check IAM user has `AmazonBedrockFullAccess` policy
- Ensure no spaces or quotes around credentials

### Error: "Region not supported"
- Change `AWS_REGION` to `us-east-1`
- Not all regions have Bedrock

### Error: "Throttling exception"
- AWS has rate limits
- Wait a few seconds and retry
- Consider upgrading AWS support tier

## ✅ Verification Commands

**Test AWS Credentials:**
```bash
python -c "import boto3; client = boto3.client('bedrock-runtime', region_name='us-east-1'); print('✓ AWS credentials valid')"
```

**Test Bedrock Access:**
```bash
python -c "import boto3, json; client = boto3.client('bedrock-runtime', region_name='us-east-1'); response = client.invoke_model(modelId='anthropic.claude-3-5-sonnet-20241022-v2:0', body=json.dumps({'anthropic_version': 'bedrock-2023-05-31', 'max_tokens': 100, 'messages': [{'role': 'user', 'content': 'Say OK'}]})); print('✓ Bedrock access granted')"
```

---

**You're all set! The agent now uses AWS Bedrock for all AI operations.** 🚀
