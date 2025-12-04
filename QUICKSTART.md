# 🚀 Quick Start Guide - Bug Reproduction Agent

**Get from zero to automated bug reproduction in under 10 minutes!**

## What This Does

This agent:
1. Reads bug reports from JIRA
2. Extracts application URL and reproduction steps
3. Opens your application in a real browser
4. Executes the bug reproduction steps automatically
5. Reports if the bug was reproduced with screenshots

## ⚡ 5-Step Setup

### Step 1: Install Python Packages (2 min)

```bash
# Navigate to project
cd c:\Users\z004drkc\IBM_POC\debugger-agent

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### Step 2: Get API Keys (3 min)

**Anthropic API Key:**
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Create API key
4. Copy key (starts with `sk-ant-...`)

**JIRA API Token:**
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Copy token (starts with `ATATT...`)

### Step 3: Configure Environment (1 min)

Create `.env` file in project root:

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-...your-key...

# JIRA Configuration
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=ATATT...your-token...
JIRA_PROJECT_KEY=KAN

# Browser Settings
HEADLESS_BROWSER=false
AUTO_POST_TO_JIRA=false
```

### Step 4: Test Setup (1 min)

```bash
cd agent
python setup_check.py
```

You should see all ✓ checks pass.

### Step 5: Run First Bug Reproduction (2 min)

```bash
# Replace KAN-4 with your JIRA issue key
python bug_reproduction_agent.py KAN-4
```

## What to Expect

The agent will:
1. ✓ Fetch JIRA ticket KAN-4
2. ✓ Extract application URL and steps
3. ✓ Launch Chrome browser (you'll see it!)
4. ✓ Execute each reproduction step
5. ✓ Take screenshots
6. ✓ Analyze if bug reproduced
7. ✓ Display comprehensive report

## 📖 Basic Commands

### Show Workflow Diagram
```bash
python reproduce_bug_cli.py --workflow
```

### Reproduce a Bug
```bash
python reproduce_bug_cli.py <ISSUE-KEY>
```

### With Code Context
```bash
python reproduce_bug_cli.py KAN-4 --code app.py utils.py
```

### Interactive Mode
```bash
python reproduce_bug_cli.py --interactive
```

### Verbose Output
```bash
python reproduce_bug_cli.py KAN-4 --verbose
```

## 🔑 Getting API Keys

### Anthropic API Key (Required)
1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Navigate to API Keys section
4. Click "Create Key"
5. Copy the key (starts with `sk-ant-`)
6. Add to `.env`: `ANTHROPIC_API_KEY=sk-ant-...`

### JIRA API Token (Required)
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Bug Agent")
4. Copy the token
5. Add to `.env`: `JIRA_API_TOKEN=...`

## 📊 Example Output

```
🤖 Bug Reproduction Agent
Issue: KAN-4
LLM: Claude Sonnet 4.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Starting reproduction workflow...

✓ Successfully fetched JIRA issue KAN-4
✓ Parsed 5 reproduction steps
✓ Created reproduction plan with 5 steps

Executing Step 1: Open application homepage...
    ✓ SUCCESS: Homepage loaded successfully

...

======================================
=== REPRODUCTION RESULT ===
======================================
Bug Reproduced: YES ✓
Confidence: 85%

Root Cause Analysis:
  The bug is caused by a null pointer exception...

Recommendations:
  1. Add null checks before accessing user object
  2. Implement proper error handling
  3. Add unit tests for edge cases

✓ Results saved to: results/KAN-4_result.json
```

## 🎯 Common Use Cases

### 1. Quick Bug Check
```bash
python reproduce_bug_cli.py PROJ-123
```

### 2. Deep Analysis with Code
```bash
python reproduce_bug_cli.py PROJ-123 --code src/main.py src/utils.py --verbose
```

### 3. Batch Processing
```bash
python reproduce_bug_cli.py --interactive

> PROJ-123
> PROJ-124
> PROJ-125
> exit
```

### 4. CI/CD Integration
```python
from bug_reproduction_agent import BugReproductionAgent

agent = BugReproductionAgent()
result = agent.reproduce_bug("PROJ-123")

if result["reproduction_result"]["bug_reproduced"]:
    # Update ticket status
    # Notify team
    pass
```

## 🐛 Troubleshooting

### Import Errors
```bash
# Reinstall dependencies
pip install -r ../requirements.txt --upgrade
```

### API Key Issues
- Check `.env` file has no extra spaces
- Ensure keys don't have quotes around them
- Verify keys are active in respective platforms

### JIRA Connection Failed
- Verify `JIRA_URL` includes `https://`
- Check email and token are correct
- Ensure you have access to the project

### "Issue not found"
- Verify issue key exists (e.g., `KAN-4`)
- Check you have permission to view it
- Ensure `JIRA_PROJECT_KEY` is correct

## 📚 Next Steps

1. **Read Full Documentation**: See [AGENT_GUIDE.md](AGENT_GUIDE.md)
2. **Customize Prompts**: Edit nodes in `*_node.py` files
3. **Add Real Browser Automation**: Integrate Selenium/Playwright
4. **Extend Workflow**: Add custom nodes to LangGraph
5. **Deploy**: Set up as a service for automatic bug triage

## 💡 Tips

- Use `--verbose` flag for debugging
- Save results are in `results/` directory
- Set `AUTO_POST_TO_JIRA=true` to auto-comment on tickets
- Include relevant code files for better analysis
- Use interactive mode for rapid testing

## 🤝 Need Help?

1. Run setup test: `python test_setup.py`
2. Check API connections: `python test_connection.py`
3. Review logs in verbose mode: `--verbose`
4. Read full guide: [AGENT_GUIDE.md](AGENT_GUIDE.md)

## 🎉 Success Checklist

- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Setup test passes
- [ ] First bug reproduced
- [ ] Results saved successfully

---

Ready to reproduce bugs automatically! 🚀
