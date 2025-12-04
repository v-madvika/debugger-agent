# Bug Reproduction Agent - Complete Modification Summary

## 🎯 Core Requirement Implemented

**"Application details and bug details will be given in the JIRA ticket only... access the JIRA using JIRA REST APIs, use the application link and recreate the steps mentioned in the JIRA ticket"**

## ✅ What Was Modified

### 1. Enhanced JIRA Client (`jira_client.py`)

**Key Changes:**
- Added comprehensive JIRA REST API methods
- Implemented `get_issue()` with full field expansion
- Added `get_issue_attachments()` for file retrieval
- Added `get_issue_comments()` for additional context
- Added `get_issue_transitions()` for status management
- **NEW**: `extract_application_url()` - Automatically finds app URL in JIRA ticket
  - Searches description field
  - Searches custom fields
  - Searches environment field
  - Uses regex to extract URLs

**Result:** Agent now fetches ALL information from JIRA including application URL.

### 2. Enhanced JIRA Parser (`jira_parser_node.py`)

**Key Changes:**
- Modified `parse_with_claude()` to prioritize application URL extraction
- Enhanced prompt to explicitly require application URL
- Added URL validation before proceeding
- Extracts credentials if mentioned in JIRA ticket
- Improved context gathering from comments
- **Critical**: Aborts workflow if no application URL found

**Result:** Parser ensures application URL is present before attempting reproduction.

### 3. Updated Reproduction Planner (`planner_node.py`)

**Key Changes:**
- Completely rewrote prompt to create EXECUTABLE browser automation steps
- Added specific action types: navigate, click, input, select, wait, verify, screenshot
- Added selector format specifications (CSS, XPath, text, ID, name)
- Validates that application URL is available
- Creates steps that use actual application URL from JIRA
- Generates browser-ready automation commands

**Result:** Plans are now executable by real browser automation tools.

### 4. Real Browser Automation (`browser_automation.py` - NEW FILE)

**Key Features:**
- Uses Playwright for cross-browser automation
- Supports multiple selector formats (CSS, XPath, text-based)
- Implements all action types:
  - `navigate`: Go to application URL
  - `click`: Click buttons/links
  - `input`: Enter text in fields
  - `select`: Choose dropdown options
  - `wait`: Wait for elements
  - `verify`: Check element visibility
  - `screenshot`: Capture evidence
  - `execute_js`: Run JavaScript
- Automatic screenshot capture at each step
- Error screenshots on failures
- Real browser interaction with actual application

**Result:** Agent now interacts with REAL applications using URLs from JIRA.

### 5. Enhanced Execution Node (`execution_node.py`)

**Key Changes:**
- Added `execute_steps_with_browser()` for real automation
- Integrated Playwright browser automation
- Maintains simulation fallback for testing
- Captures and reports execution results
- Collects screenshots as evidence
- Reports success/failure for each step

**Result:** Steps are executed on actual application, not simulated.

### 6. Updated Main Agent (`bug_reproduction_agent.py`)

**Key Changes:**
- Added `use_real_browser` parameter (default: True)
- Enhanced initialization logging
- Improved command-line interface
- Added `--simulate` flag for testing without browser
- Better error reporting
- Status messages show real vs simulation mode

**Result:** Clear control over execution mode with real browser as default.

### 7. Updated Dependencies (`requirements.txt`)

**Added:**
- `playwright>=1.40.0` - Browser automation
- `selenium>=4.15.0` - Alternative automation (optional)

**Result:** All required packages for browser automation included.

### 8. Documentation Updates

**Modified Files:**
- `README.md`: Complete rewrite with JIRA-focused workflow
- `QUICKSTART.md`: Updated with new setup steps
- Created `setup_check.py`: Automated setup verification

**Result:** Clear documentation of JIRA-driven workflow.

## 🔄 Complete Workflow (As Implemented)

```
1. JIRA REST API Call
   └─> Fetch ticket with all fields (KAN-4)
   └─> Extract application URL from description/custom fields
   └─> Get reproduction steps from description
   └─> Get expected/actual behavior

2. Claude AI Parsing
   └─> Parse reproduction steps into structured format
   └─> Validate application URL is present
   └─> Extract any credentials mentioned
   └─> Structure for automation

3. Reproduction Planning
   └─> Convert steps to browser automation commands
   └─> Specify exact selectors (CSS, XPath, etc.)
   └─> Add verification points
   └─> Include screenshot commands

4. Real Browser Execution
   └─> Launch Playwright browser
   └─> Navigate to application URL (from JIRA)
   └─> Execute each step:
       - Click buttons
       - Enter text
       - Select options
       - Verify elements
   └─> Capture screenshots at each step
   └─> Record errors

5. Bug Verification
   └─> Compare expected vs actual results
   └─> AI analyzes if bug reproduced
   └─> Generate confidence score

6. Report Generation
   └─> Create detailed report
   └─> Include screenshots
   └─> Optionally post to JIRA as comment
```

## 💡 Key Features Implemented

### ✅ 100% JIRA-Driven
- All information from JIRA tickets
- No manual configuration needed per bug
- Application URL extracted automatically

### ✅ Real Browser Automation
- Uses Playwright (industry-standard)
- Supports Chrome, Firefox, Safari
- Real UI interactions
- Screenshot evidence

### ✅ Application Access
- Navigates to actual application
- Uses URL from JIRA ticket
- Handles login if credentials in JIRA
- Works with any web application

### ✅ Flexible Execution
- Real browser mode (default)
- Simulation mode for testing
- Headless or visible browser
- Configurable timeouts

### ✅ Comprehensive Reporting
- Step-by-step execution log
- Screenshots at each step
- Root cause analysis
- Fix recommendations
- Optional JIRA posting

## 🎮 Usage Examples

### Basic Usage
```bash
cd agent
python bug_reproduction_agent.py KAN-4
```

### With Different Tickets
```bash
python bug_reproduction_agent.py PROJ-123
python bug_reproduction_agent.py BUG-42
```

### Simulation Mode (Testing)
```bash
python bug_reproduction_agent.py KAN-4 --simulate
```

### Check Setup
```bash
python setup_check.py
```

## 📋 JIRA Ticket Requirements

For best results, JIRA tickets should include:

1. **Application URL** (REQUIRED)
   - In description: "Application: https://myapp.com"
   - In custom field: "App URL"
   - In environment field

2. **Reproduction Steps** (REQUIRED)
   - Clear, numbered steps
   - Specific UI elements to interact with
   - Data to enter

3. **Expected Behavior**
   - What should happen

4. **Actual Behavior**
   - What actually happens (the bug)

5. **Optional**
   - Login credentials
   - Browser/OS information
   - Screenshots/attachments

## 🔧 Configuration Options

### Environment Variables (.env)
```env
# REQUIRED
ANTHROPIC_API_KEY=...        # Claude AI access
JIRA_URL=...                 # JIRA instance
JIRA_EMAIL=...               # JIRA login
JIRA_API_TOKEN=...           # JIRA API token
JIRA_PROJECT_KEY=...         # Project key

# OPTIONAL
HEADLESS_BROWSER=false       # Show/hide browser
AUTO_POST_TO_JIRA=false      # Auto-post results
```

## 📊 Success Criteria Met

✅ Accesses JIRA using REST APIs
✅ Extracts application details from JIRA ticket
✅ Extracts bug details from JIRA ticket
✅ Uses application link from JIRA
✅ Recreates steps mentioned in JIRA ticket
✅ Executes on actual application
✅ Reports results with evidence

## 🚀 Next Steps

1. **Test with Your JIRA**
   - Update .env with your credentials
   - Run setup_check.py
   - Try with a test ticket

2. **Create Test Tickets**
   - Add application URLs
   - Include clear reproduction steps
   - Test with simple bugs first

3. **Integrate into Workflow**
   - Run on new bug tickets
   - Schedule regular runs
   - Post results back to JIRA

## 📞 Support

If issues arise:
1. Run `python setup_check.py` to verify configuration
2. Check .env has all required variables
3. Ensure JIRA tickets have application URLs
4. Try simulation mode first: `--simulate`
5. Check screenshots/ directory for execution evidence

---

**Implementation Complete**: All requirements met for JIRA-driven bug reproduction with real browser automation.
