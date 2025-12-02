# 🤖 FREE Debug Agent - AI-Powered Bug Investigation

> A 100% FREE proof-of-concept AI debugging agent that integrates Jira, GitHub, and Claude AI to automate bug investigation and documentation.

## ✨ Features

- 🔍 **Automated Bug Investigation** - Analyzes Jira tickets and suggests root causes
- 💻 **Code Analysis** - Reviews code files and recent commits
- 📝 **Solution Documentation** - Automatically documents fixes in Jira
- 🚀 **100% FREE** - Works with free tiers of Jira, GitHub, and AWS Bedrock
- 🎯 **No MCP Server Required** - Direct API integration for simplicity

## 🛠️ Tech Stack

- **AI Model**: Claude 3.5 Sonnet (via AWS Bedrock)
- **Issue Tracking**: Atlassian Jira (Free tier)
- **Version Control**: GitHub (Free tier)
- **Language**: Python 3.8+

## 📋 Prerequisites

- Python 3.8 or higher
- AWS Account (Free tier eligible)
- Jira Account (Free - up to 10 users)
- GitHub Account (Free)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/v-madvika/SmartTasks.git
cd "Debugger Agent"
```

### 2. Create Virtual Environment

**Windows:**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy the example environment file
cp .env.example agent/.env

# Edit agent/.env and add your API keys
```

#### Getting API Keys:

**AWS Bedrock (Recommended):**
1. Create AWS account at https://aws.amazon.com
2. Go to IAM → Users → Create Access Key
3. Add `BedrockFullAccess` permission
4. Copy Access Key ID and Secret Access Key

**Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy the token

**GitHub Token:**
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select `repo` scope
4. Copy the token

### 5. Test the Agent

```bash
cd agent
python test_connection.py
```

## 📖 Usage Examples

### Test Connection to All Services

```bash
python test_connection.py
```

### Investigate a Bug

```python
from cli import FreeDebugAgent

agent = FreeDebugAgent()
agent.investigate_bug('KAN-4')
```

### Analyze Bug with Code

```python
code_files = {
    'app.py': open('app.py').read(),
    'utils.py': open('utils.py').read()
}

agent.analyze_with_code('KAN-4', code_files)
```

### Full Workflow (Investigate → Analyze → Document)

```python
agent.full_workflow('KAN-4', code_files)
```

## 📁 Project Structure

```
Debugger Agent/
├── agent/
│   ├── cli.py              # Main agent CLI
│   ├── jira_client.py      # Jira API integration
│   ├── github_client.py    # GitHub API integration
│   ├── test_connection.py  # Connection tests
│   └── .env               # Your config (not in Git!)
├── requirements.txt        # Python dependencies
├── .env.example           # Config template
├── .gitignore            # Git ignore rules
├── SETUP.md              # Detailed setup guide
└── README.md             # This file
```

## 🧪 Testing

Run the test suite:

```bash
cd agent
python test_connection.py  # Test all connections
python test_kan4.py       # Test specific issue retrieval
```

## 🔒 Security Notes

- ⚠️ **NEVER commit `.env` files** - They contain sensitive credentials
- ✅ Always use `.env.example` as a template
- ✅ The `.gitignore` file prevents accidental commits
- ✅ Rotate API tokens regularly
- ✅ Use AWS IAM with minimal required permissions

## 🐛 Troubleshooting

### "Bad credentials" error
- Verify your tokens are correct and not expired
- Check that tokens have the required permissions

### "Issue does not exist" error
- Verify the issue key exists in Jira
- Check project permissions

### "Module not found" error
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt`

See [SETUP.md](SETUP.md) for detailed troubleshooting.

## 📝 License

This project is a proof-of-concept (POC) for educational purposes.

## 🤝 Contributing

This is a POC project. Feel free to fork and adapt for your needs!

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

**Made with ❤️ using Claude AI**
