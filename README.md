# AI Bug Reproduction Agent - Automated Bug Testing from JIRA

## 🎯 Overview

**100% JIRA-Driven Bug Reproduction System**

The AI Bug Reproduction Agent is a fully automated system that:
1. **Fetches** bug reports directly from JIRA via REST API
2. **Extracts** application URL, reproduction steps, and bug details from JIRA tickets
3. **Understands** the steps using Claude Sonnet 4.0 AI
4. **Accesses** your actual application using the URL from JIRA
5. **Executes** reproduction steps with real browser automation (Playwright)
6. **Verifies** if the bug occurs on the real application
7. **Reports** results back to JIRA with screenshots and analysis

## 🔑 Key Features

- ✅ **Zero Manual Configuration**: All details from JIRA tickets
- ✅ **Real Browser Automation**: Uses Playwright for actual UI interactions
- ✅ **Application URL Extraction**: Automatically finds app URL from JIRA
- ✅ **Screenshot Evidence**: Captures screenshots at each step
- ✅ **AI-Powered Analysis**: Claude Sonnet 4.0 for root cause analysis
- ✅ **JIRA Integration**: Posts results back to JIRA automatically

## 🔄 Complete Workflow

```
┌─────────────────────────────────┐
│  JIRA Ticket (KAN-4)            │
│  ┌──────────────────────────┐   │
│  │ Summary: Login bug       │   │
│  │ Description: Steps...    │   │
│  │ App URL: http://app.com  │   │
│  │ Expected: Login success  │   │
│  │ Actual: Error 500        │   │
│  └──────────────────────────┘   │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  1. JIRA REST API Fetch         │
│  - Get full ticket details      │
│  - Extract application URL      │
│  - Get reproduction steps       │
│  - Get expected/actual behavior │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  2. Claude AI Parsing           │
│  - Understand reproduction steps│
│  - Extract technical details    │
│  - Identify application URL     │
│  - Plan executable steps        │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  3. Reproduction Planning       │
│  - Convert to automation steps  │
│  - Identify UI elements         │
│  - Create browser actions       │
│  - Add verification points      │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  4. REAL BROWSER EXECUTION      │
│  - Launch Playwright browser    │
│  - Navigate to app URL          │
│  - Execute each step            │
│  - Capture screenshots          │
│  - Record errors                │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  5. Bug Verification            │
│  - Compare expected vs actual   │
│  - AI analyzes results          │
│  - Determine if bug reproduced  │
│  - Generate confidence score    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  6. Report to JIRA              │
│  - Post comment with findings   │
│  - Attach screenshots           │
│  - Include root cause analysis  │
│  - Add recommendations          │
└─────────────────────────────────┘
```

## 📋 Prerequisites

### Required Services:

1. **JIRA Account** (Free - up to 10 users)
   - JIRA instance URL (e.g., https://yourcompany.atlassian.net)
   - API token for authentication
   - Project with bug tickets

2. **Anthropic API Key**
   - Claude Sonnet 4.0 access
   - Get from: https://console.anthropic.com/

3. **Application Access**
   - URL to your application (from JIRA ticket)
   - Test environment credentials (if required)
   - Network access to the application

### System Requirements:
- **Python 3.8+** installed
- **Windows/Mac/Linux** supported
- **Chrome/Firefox** browser installed (for Playwright)
- **4GB+ RAM** recommended
- **Internet connection**

### Optional:
- **AWS Bedrock** (for AWS-hosted Claude)
- **GitHub** (for version control)

## 🚀 Setup Instructions

### Step 1: Clone the Repository

```bash
cd c:\Users\z004drkc\IBM_POC
git clone <your-repo-url> debugger-agent
cd debugger-agent
```

### Step 2: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

**Required packages:**
```txt
boto3>=1.28.0              # AWS Bedrock
anthropic>=0.7.0           # Claude SDK
jira>=3.5.0                # Jira API
selenium>=4.15.0           # UI automation
playwright>=1.40.0         # Modern web automation
requests>=2.31.0           # API testing
pillow>=10.0.0             # Screenshots
python-dotenv>=1.0.0       # Environment variables
```

### Step 3: Get Anthropic API Key

1. **Sign up for Anthropic:**
   - Visit: https://console.anthropic.com/
   - Create account or sign in
   - Navigate to API Keys section

2. **Create API Key:**
   - Click "Create Key"
   - Name it "Bug Reproduction Agent"
   - Copy the key (starts with `sk-ant-...`)
   - Store securely

### Step 4: Configure JIRA

1. **Get JIRA API Token:**
   - Visit: https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Name it "Bug Reproduction Agent"
   - Copy the token (starts with `ATATT...`)

2. **Find Your JIRA Details:**
   - **JIRA URL**: Your instance URL (e.g., `https://yourcompany.atlassian.net`)
   - **Email**: Your JIRA login email
   - **Project Key**: Your project key (e.g., `KAN`, `PROJ`, `BUG`)

3. **Create Test JIRA Ticket:**
   Create a bug ticket with:
   - **Summary**: Brief bug description
   - **Description**: Include application URL and reproduction steps
   - **Expected Behavior**: What should happen
   - **Actual Behavior**: What actually happens (the bug)

### Step 5: Create Environment File

Create a `.env` file in the project root:

```bash
notepad .env
```

**Required Configuration:**

```dotenv
# ============================================
# ANTHROPIC API (REQUIRED)
# ============================================
ANTHROPIC_API_KEY=sk-ant-...your-api-key...

# ============================================
# JIRA CONFIGURATION (REQUIRED)
# ============================================
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your-email@company.com
JIRA_API_TOKEN=ATATT...your-jira-token...
JIRA_PROJECT_KEY=KAN

# ============================================
# BROWSER SETTINGS
# ============================================
HEADLESS_BROWSER=false
# Set to 'true' to run browser in background
# Set to 'false' to see browser actions in real-time

# ============================================
# JIRA AUTO-POSTING (OPTIONAL)
# ============================================
AUTO_POST_TO_JIRA=false
# Set to 'true' to automatically post results to JIRA
# Set to 'false' to only display results locally

# ============================================
# AWS BEDROCK (OPTIONAL - Alternative to Anthropic)
# ============================================
# USE_BEDROCK=false
# AWS_ACCESS_KEY_ID=AKIA...
# AWS_SECRET_ACCESS_KEY=...
# AWS_REGION=us-east-1
```

### Step 6: Install Playwright Browsers

```bash
# Install Playwright browser binaries
playwright install chromium

# Or install all browsers (Chrome, Firefox, Safari)
playwright install
```

This downloads the browser binaries needed for automation.

## 🎮 Usage

### Quick Start

Run bug reproduction for a specific JIRA ticket:

```bash
# Navigate to agent directory
cd agent

# Run with real browser (recommended)
python bug_reproduction_agent.py KAN-4

# Run with AI simulation (no browser)
python bug_reproduction_agent.py KAN-4 --simulate
```

### What Happens:

1. **Fetches JIRA ticket** `KAN-4` via REST API
2. **Extracts application URL** from ticket description/fields
3. **Parses reproduction steps** using Claude AI
4. **Launches browser** and navigates to application
5. **Executes each step** (clicks, inputs, verifications)
6. **Takes screenshots** at each step
7. **Analyzes results** and determines if bug reproduced
8. **Generates report** with root cause and recommendations

### Example Output:

```
🤖 Bug Reproduction Agent - JIRA Edition
============================================================
Issue: KAN-4
Mode: Real Browser
============================================================

✓ JIRA Client initialized: https://madvika.atlassian.net
✓ Project: KAN
✓ Fetching JIRA issue: KAN-4
✓ Successfully fetched JIRA issue KAN-4
✓ Parsed 5 reproduction steps
  Application: MyWebApp
  Platform: web
  🌐 Application URL: https://myapp.example.com

Creating detailed reproduction plan with Claude...
✓ Created reproduction plan with 7 steps

============================================================
  REAL BROWSER AUTOMATION - Executing on actual application
============================================================

  Step 1: Navigate to application homepage
    ✓ SUCCESS: Navigated to https://myapp.example.com

  Step 2: Click on login button
    ✓ SUCCESS: Clicked on css:#login-btn

  Step 3: Enter username
    ✓ SUCCESS: Entered text in css:#username

  Step 4: Enter password
    ✓ SUCCESS: Entered text in css:#password

  Step 5: Click submit button
    ✓ SUCCESS: Clicked on css:#submit

  Step 6: Verify error message
    ✗ FAILED: Element css:.error-message not found

============================================================
=== REPRODUCTION RESULT ===
============================================================
Bug Reproduced: YES ✓
Confidence: 85%

Root Cause Analysis:
  The login form accepts invalid credentials but displays 
  an error message that is not visible in the DOM...

Recommendations:
  1. Fix error message display CSS
  2. Add proper error handling
  3. Validate inputs on server-side

Screenshots saved to: screenshots/
============================================================
```

### Command-Line Options

```bash
# Basic usage - real browser
python bug_reproduction_agent.py <ISSUE_KEY>

# Examples
python bug_reproduction_agent.py KAN-4
python bug_reproduction_agent.py PROJ-123
python bug_reproduction_agent.py BUG-42

# Simulation mode (no browser)
python bug_reproduction_agent.py KAN-4 --simulate

# Process multiple tickets
python main.py

# Process specific ticket
python main.py --ticket KAN-123

# Process tickets with specific label
python main.py --label "needs-reproduction"

# Dry run (no Jira updates)
python main.py --dry-run
```

### Advanced Usage

```bash
# Process tickets from specific sprint
python main.py --sprint "Sprint 5"

# Filter by priority
python main.py --priority High,Critical

# Continuous monitoring mode
python main.py --watch --interval 300  # Check every 5 minutes

# Custom browser
python main.py --browser firefox

# Headless mode (no UI)
python main.py --headless
```

## 📊 How It Works

### Example Jira Ticket Format

**Ticket: KAN-123**
```
Summary: Login fails with valid credentials

Description:
Users are unable to login even with correct username and password.

Reproduction Steps:
1. Go to https://app.example.com/login
2. Enter email: test@example.com
3. Enter password: Test123!
4. Click "Login" button
5. Observe: Error message "Invalid credentials" appears

Expected Result:
User should be logged in and redirected to dashboard

Actual Result:
Error message shown, user remains on login page

Environment:
- Browser: Chrome 120
- OS: Windows 11
```

### Agent Processing Flow

#### 1. **Fetch Jira Ticket**
```python
# Agent reads ticket KAN-123
ticket = jira.get_ticket("KAN-123")
steps = ticket.fields.description  # Extracts reproduction steps
```

#### 2. **AI Understanding (Claude Sonnet 4.0)**
```json
{
  "understood_steps": [
    {
      "step": 1,
      "action": "navigate",
      "target": "https://app.example.com/login",
      "type": "url"
    },
    {
      "step": 2,
      "action": "input",
      "target": "email_field",
      "value": "test@example.com",
      "selector": "input[name='email']"
    },
    {
      "step": 3,
      "action": "input",
      "target": "password_field",
      "value": "Test123!",
      "selector": "input[type='password']"
    },
    {
      "step": 4,
      "action": "click",
      "target": "login_button",
      "selector": "button[type='submit']"
    },
    {
      "step": 5,
      "action": "verify",
      "target": "error_message",
      "expected": "Invalid credentials"
    }
  ],
  "test_type": "ui_automation",
  "estimated_time": "30 seconds"
}
```

#### 3. **Execute Test Automation**
```python
# Agent executes steps using Playwright/Selenium
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Step 1: Navigate
    page.goto("https://app.example.com/login")
    page.screenshot(path="screenshots/step1.png")
    
    # Step 2: Enter email
    page.fill("input[name='email']", "test@example.com")
    page.screenshot(path="screenshots/step2.png")
    
    # Step 3: Enter password
    page.fill("input[type='password']", "Test123!")
    page.screenshot(path="screenshots/step3.png")
    
    # Step 4: Click login
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")
    page.screenshot(path="screenshots/step4.png")
    
    # Step 5: Verify error
    error = page.locator(".error-message").text_content()
    
    browser.close()
```

#### 4. **Analyze Results**
```json
{
  "bug_reproduced": true,
  "confidence": 0.95,
  "evidence": [
    "screenshots/step1.png",
    "screenshots/step2.png",
    "screenshots/step3.png",
    "screenshots/step4.png"
  ],
  "actual_error": "Invalid credentials",
  "expected_behavior": "Successful login",
  "execution_time": "28 seconds",
  "additional_findings": [
    "Network request returned 401 status",
    "Console error: 'Authentication failed'"
  ]
}
```

#### 5. **Update Jira Ticket**
```python
# Add comment with results
comment = """
🤖 **Automated Bug Reproduction Results**

✅ **Bug Successfully Reproduced**

**Execution Time:** 28 seconds
**Confidence:** 95%

**Steps Executed:**
1. ✅ Navigated to login page
2. ✅ Entered email: test@example.com
3. ✅ Entered password: ****
4. ✅ Clicked login button
5. ✅ Verified error message

**Findings:**
- Error message displayed: "Invalid credentials"
- HTTP Status: 401 Unauthorized
- Console Error: "Authentication failed"

**Evidence:**
See attached screenshots for each step.

**Recommendation:**
Bug confirmed. Assigning to backend team for investigation.
"""

jira.add_comment("KAN-123", comment)
jira.add_attachments("KAN-123", screenshots)
jira.update_status("KAN-123", "In Progress")
jira.assign("KAN-123", "backend-team")
```

## 🔧 Configuration

### Application Types Supported

#### 1. **Web Applications (UI Testing)**
```yaml
# config/app_config.yaml
app_type: web_ui
base_url: https://staging.yourapp.com
browser: chrome
headless: false
viewport:
  width: 1920
  height: 1080
```

#### 2. **REST APIs**
```yaml
app_type: rest_api
base_url: https://api.yourapp.com
auth:
  type: bearer_token
  token: ${API_TOKEN}
```

#### 3. **Mobile Apps (via Appium)**
```yaml
app_type: mobile
platform: android
app_path: /path/to/app.apk
device: emulator-5554
```

### Custom Selectors

Create `config/selectors.yaml` for your application:
```yaml
login_page:
  email_input: "input[name='email']"
  password_input: "input[type='password']"
  login_button: "button[type='submit']"
  error_message: ".alert-danger"

dashboard:
  welcome_text: "h1.welcome"
  user_menu: "#user-dropdown"
```

## 📝 Jira Ticket Best Practices

### Good Reproduction Steps Format

✅ **GOOD:**
```
Reproduction Steps:
1. Navigate to Login page (https://app.com/login)
2. Enter email: "test@example.com" in email field
3. Enter password: "Test123!" in password field
4. Click the "Login" button
5. Observe the error message displayed

Expected: User logs in successfully
Actual: Error "Invalid credentials" appears
```

❌ **BAD:**
```
Reproduction Steps:
The login doesn't work. I tried logging in but it failed.
```

### Required Information

The agent looks for:
- **Clear step-by-step instructions** (numbered)
- **Specific URLs** or page names
- **Exact values** to input (emails, passwords, text)
- **Element descriptions** (buttons, fields, links)
- **Expected vs Actual results**

## 🎯 Supported Jira Fields

### Agent Reads:
- `summary` - Bug title
- `description` - Reproduction steps
- `priority` - To prioritize testing
- `labels` - To filter tickets
- `environment` - Browser, OS info
- `custom_fields` - App version, etc.

### Agent Updates:
- `comments` - Test results
- `attachments` - Screenshots, videos
- `status` - "Reproduced" / "Cannot Reproduce"
- `labels` - Adds "auto-reproduced"
- `assignee` - Routes to team

## 🐛 Troubleshooting

### Agent Can't Understand Steps

**Issue:** "Unable to parse reproduction steps"

**Solution:**
- Ensure steps are numbered (1, 2, 3...)
- Use clear action words (Click, Enter, Navigate, Select)
- Provide specific selectors or descriptions
- Add expected vs actual results

### Application Element Not Found

**Issue:** "Element not found: login_button"

**Solution:**
```bash
# Run in debug mode to see what's on the page
python main.py --ticket KAN-123 --debug --no-headless

# Update selectors in config/selectors.yaml
# Or let Claude learn the page structure
python scripts/learn_page.py --url https://app.com/login
```

### Bug Cannot Be Reproduced

**Issue:** Agent says "Cannot reproduce"

**Possible Causes:**
- Bug is environment-specific (production vs staging)
- Timing issue (need to wait longer)
- Data dependency (specific user/account needed)
- Browser-specific (Chrome vs Firefox)

**Solution:**
```bash
# Try different browser
python main.py --ticket KAN-123 --browser firefox

# Add wait times
python main.py --ticket KAN-123 --slow-mo 1000

# Use specific test data
# Edit .env: TEST_USER_EMAIL=specific-user@example.com
```

## 📊 Reporting & Analytics

### View Reproduction Statistics

```bash
# Generate report for last 30 days
python scripts/generate_report.py --days 30

# Output:
# ========================================
# Bug Reproduction Report
# ========================================
# Total Tickets Processed: 47
# Successfully Reproduced: 38 (81%)
# Cannot Reproduce: 6 (13%)
# Errors/Timeouts: 3 (6%)
# 
# Average Reproduction Time: 45 seconds
# Total Time Saved: 23.5 hours
# ========================================
```

### Dashboard

Access web dashboard:
```bash
python dashboard/app.py
# Open: http://localhost:5000
```

## 💡 Advanced Features

### 1. **Video Recording**
```python
# Enable video recording of reproduction
VIDEO_RECORDING=True
```

### 2. **AI-Powered Exploration**
```python
# If steps are vague, let Claude explore the app
AUTO_EXPLORE=True
```

### 3. **Network Traffic Capture**
```python
# Capture API calls during reproduction
CAPTURE_NETWORK=True
```

### 4. **Performance Metrics**
```python
# Track page load times, response times
TRACK_PERFORMANCE=True
```

## 🔒 Security

### Test Environment Best Practices

1. **Use Staging/Test Environment**
   - Never run on production
   - Use test data only

2. **Secure Credentials**
   - Store test credentials in `.env`
   - Rotate regularly
   - Use dedicated test accounts

3. **Rate Limiting**
   - Don't overwhelm your application
   - Add delays between actions

## 💰 Cost Estimation

### AWS Bedrock Costs (After Free Tier)
- **Input tokens:** ~$0.003 per 1K tokens
- **Output tokens:** ~$0.015 per 1K tokens
- **Average per ticket:** ~$0.05
- **100 tickets/month:** ~$5

### Optimization:
- Cache similar reproduction steps
- Batch process tickets
- Use smaller context windows

## 📚 Example Use Cases

### 1. Daily Bug Triage
```bash
# Morning routine: Test all new bugs
python main.py --label "new-bug" --auto-assign
```

### 2. Release Validation
```bash
# Before release: Verify all fixed bugs
python main.py --status "Fixed" --label "needs-verification"
```

### 3. Regression Testing
```bash
# After deployment: Check known issues
python main.py --label "regression-candidate"
```

## 🤝 Integration

### CI/CD Pipeline
```yaml
# .github/workflows/bug-reproduction.yml
name: Automated Bug Reproduction
on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  reproduce-bugs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Bug Reproduction Agent
        run: |
          python main.py --label "needs-reproduction"
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
```

## 📞 Support

Need help?
1. Check logs: `logs/agent.log`
2. Run with debug: `--debug --verbose`
3. Review screenshots: `screenshots/` directory

## 📄 License

MIT License
