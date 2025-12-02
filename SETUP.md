# FREE Debug Agent - Setup Instructions

## Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

## Project Structure
```
Debugger Agent/
├── requirements.txt    # Install from here
├── .env.example
├── agent/
│   ├── .env           # Your actual config
│   ├── cli.py
│   ├── jira_client.py
│   └── github_client.py
└── venv/              # Created by you
```

## Setup Steps

### 1. Navigate to Project Root
```cmd
cd "c:\Projects\POC\Debugger Agent"
```

### 2. Create Virtual Environment

**Windows (PowerShell/CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (Git Bash):**
```bash
python -m venv venv
source venv/Scripts/activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
**Make sure you're in the project root directory!**
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
1. Copy `.env.example` to `agent/.env`
2. Fill in your actual API keys and tokens

#### Getting API Keys/Tokens:

**GitHub Personal Access Token:**
1. Go to https://github.com/settings/tokens
2. Click **"Generate new token (classic)"**
3. Give it a name (e.g., "Debug Agent")
4. Select scopes: **`repo`** (Full control of private repositories)
5. Click **"Generate token"**
6. **Copy the token immediately** (you won't see it again!)
7. Paste into `GITHUB_TOKEN` in `.env`

**Jira API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **"Create API token"**
3. Give it a label (e.g., "Debug Agent")
4. Copy the token and paste into `JIRA_API_TOKEN` in `.env`

**Anthropic API Key:**
1. Go to https://console.anthropic.com/settings/keys
2. Click **"Create Key"**
3. Copy and paste into `ANTHROPIC_API_KEY` in `.env`

### 5. Test the Agent

**Quick Connection Test:**
```bash
cd agent
python test_connection.py
```

**Test Reading KAN-4 Ticket:**
```bash
python test_kan4.py
```

**Interactive Test:**
```bash
python cli.py
```

## Deactivate Virtual Environment
```bash
deactivate
```

## Troubleshooting

**Issue:** `ERROR: Could not open requirements file`
- **Solution:** Make sure you're in the project root directory (`c:\Projects\POC\Debugger Agent`), NOT in the `agent` subdirectory
- **Check:** Run `dir` (Windows) or `ls` (Linux/Mac) - you should see `requirements.txt` listed

**Issue:** `venv/bin/activate: No such file or directory`
- **Solution:** Use the correct path for your OS (see commands above)

**Issue:** Import errors
- **Solution:** Make sure virtual environment is activated and dependencies are installed

**Issue:** `401 Bad credentials` from GitHub
- **Solution:** Your GitHub token is invalid or expired
- **Fix:** Generate a new token following the instructions above
- **Important:** Make sure to select the `repo` scope when creating the token

## Quick Start (Windows)
```cmd
cd "c:\Projects\POC\Debugger Agent"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
cd agent
python cli.py
```
