# 🤖 Bug Reproduction Agent - Complete Guide

A sophisticated AI-powered agent that automatically reproduces bugs from JIRA using LangGraph and Claude Sonnet 4.0.

## 🌟 Features

- **Intelligent JIRA Parsing**: Uses Claude Sonnet 4.0 to extract reproduction steps, expected behavior, and application details
- **Automated Planning**: Creates detailed, executable reproduction plans
- **Simulated Execution**: Simulates bug reproduction steps with AI-powered analysis
- **Root Cause Analysis**: Provides intelligent analysis of potential bug causes
- **Recommendations**: Suggests fixes and next steps
- **LangGraph Workflow**: Uses state-of-the-art agentic orchestration
- **Rich CLI**: Beautiful command-line interface with progress indicators

## 🏗️ Architecture

### LangGraph Workflow

```
┌─────────────────────────┐
│  Fetch & Parse JIRA     │
│  (JiraParserNode)       │
│  - Fetches issue data   │
│  - Extracts steps       │
│  - Parses details       │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  Create Reproduction    │
│  Plan (PlannerNode)     │
│  - Analyzes steps       │
│  - Creates plan         │
│  - Validates plan       │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  Execute Reproduction   │
│  Steps (ExecutionNode)  │
│  - Simulates execution  │
│  - Captures results     │
│  - Tracks status        │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  Generate Report        │
│  - Root cause analysis  │
│  - Recommendations      │
│  - Optional JIRA post   │
└─────────────────────────┘
```

### Components

1. **agent_state.py**: Defines all Pydantic models and TypedDict state
2. **jira_parser_node.py**: Fetches and parses JIRA issues with Claude
3. **planner_node.py**: Creates detailed reproduction plans
4. **execution_node.py**: Simulates and verifies bug reproduction
5. **bug_reproduction_agent.py**: Main LangGraph orchestrator
6. **reproduce_bug_cli.py**: Rich CLI interface

## 🚀 Installation

### Prerequisites

- Python 3.9+
- JIRA account with API access
- Anthropic API key (Claude Sonnet 4.0)

### Step 1: Install Dependencies

```bash
cd agent
pip install -r ../requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file in the `agent` directory:

```bash
# Copy example
cp .env.example .env

# Edit with your credentials
nano .env
```

Required environment variables:

```env
# Anthropic API Key (for Claude Sonnet 4.0)
ANTHROPIC_API_KEY=sk-ant-xxxxx

# JIRA Configuration
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-jira-token
JIRA_PROJECT_KEY=YOUR_PROJECT

# Optional: Auto-post results to JIRA
AUTO_POST_TO_JIRA=false

# Optional: GitHub (if using code context)
GITHUB_TOKEN=ghp_xxxxx
GITHUB_REPO=owner/repo
```

### Getting API Keys

#### Anthropic API Key
1. Go to https://console.anthropic.com/
2. Create an account or log in
3. Navigate to API Keys
4. Create a new key
5. Copy the key (starts with `sk-ant-`)

#### JIRA API Token
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Bug Reproduction Agent")
4. Copy the token immediately

## 📖 Usage

### Basic Usage

```bash
cd agent

# Reproduce a bug
python reproduce_bug_cli.py KAN-4
```

### With Code Context

```bash
# Include code files for better analysis
python reproduce_bug_cli.py KAN-4 --code app.py utils.py models.py
```

### Interactive Mode

```bash
# Start interactive session
python reproduce_bug_cli.py --interactive

# Then enter issue keys interactively
> KAN-4
> PROJ-123
> exit
```

### Verbose Output

```bash
# See detailed execution logs
python reproduce_bug_cli.py KAN-4 --verbose
```

### Show Workflow

```bash
# Display workflow diagram
python reproduce_bug_cli.py --workflow
```

## 🎯 CLI Commands

```bash
# Basic reproduction
python reproduce_bug_cli.py <ISSUE-KEY>

# Options
--code FILE [FILE ...]    Include code files for context
--interactive, -i         Interactive mode
--verbose, -v            Show detailed logs
--workflow               Show workflow diagram
--help                   Show help message
```

## 📊 Output

### Console Output

The agent provides rich, formatted output including:
- Real-time progress indicators
- Status updates for each node
- Formatted reproduction results
- Root cause analysis
- Recommendations

### JSON Results

Results are saved to `results/<ISSUE-KEY>_result.json`:

```json
{
  "status": "completed",
  "reproduction_result": {
    "issue_key": "KAN-4",
    "bug_reproduced": true,
    "confidence_score": 0.85,
    "root_cause_analysis": "...",
    "recommendations": ["..."],
    "executed_steps": [...]
  }
}
```

## 🔧 Advanced Configuration

### Custom Model Configuration

Edit nodes to use different Claude models:

```python
# In jira_parser_node.py, planner_node.py, execution_node.py
self.model = "claude-sonnet-4-20250514"  # or another model
```

### Enable Auto-posting to JIRA

Set in `.env`:
```env
AUTO_POST_TO_JIRA=true
```

The agent will automatically post reproduction results as JIRA comments.

### Add GitHub Integration

To include recent commits in context:

```python
from github_client import SimpleGitHubClient

github = SimpleGitHubClient()
commits = github.get_recent_commits(limit=5)

agent.reproduce_bug("KAN-4", code_files=code_files)
```

## 🧪 Testing

### Test Individual Components

```python
# Test JIRA parser
from jira_parser_node import JiraParserNode

parser = JiraParserNode()
state = {"jira_issue_key": "KAN-4", "messages": [], "errors": []}
result = parser(state)
print(result["parsed_issue"])
```

### Test Full Workflow

```bash
# Run test
cd agent
python bug_reproduction_agent.py
```

### Validate Connections

```bash
# Test all API connections
python test_connection.py
```

## 📝 Example: Complete Workflow

```python
from bug_reproduction_agent import BugReproductionAgent

# Initialize agent
agent = BugReproductionAgent()

# Optional: Load code files
code_files = {
    "app.py": open("app.py").read(),
    "utils.py": open("utils.py").read()
}

# Reproduce bug
result = agent.reproduce_bug("KAN-4", code_files=code_files)

# Access results
if result["status"] == "completed":
    repro_result = result["reproduction_result"]
    
    print(f"Bug reproduced: {repro_result['bug_reproduced']}")
    print(f"Confidence: {repro_result['confidence_score']:.0%}")
    print(f"Root cause: {repro_result['root_cause_analysis']}")
    
    for rec in repro_result["recommendations"]:
        print(f"- {rec}")
```

## 🐛 Troubleshooting

### "No module named 'langgraph'"

```bash
pip install langgraph langchain langchain-anthropic
```

### "Invalid API key"

- Verify your `ANTHROPIC_API_KEY` in `.env`
- Ensure it starts with `sk-ant-`
- Check for extra spaces or quotes

### "JIRA authentication failed"

- Verify `JIRA_URL` format (include `https://`)
- Check `JIRA_EMAIL` and `JIRA_API_TOKEN`
- Ensure API token has proper permissions

### "Issue not found"

- Verify issue key exists in JIRA
- Check `JIRA_PROJECT_KEY` matches your project
- Ensure you have permission to view the issue

### Import errors

```bash
# Ensure you're in the agent directory
cd agent

# Verify Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

## 🎨 Customization

### Add Custom Nodes

1. Create new node class:

```python
class CustomNode:
    def __call__(self, state: AgentState) -> AgentState:
        # Your logic
        return state
```

2. Add to workflow:

```python
workflow.add_node("custom", CustomNode())
workflow.add_edge("execute", "custom")
workflow.add_edge("custom", "report")
```

### Modify Prompts

Edit prompts in:
- `jira_parser_node.py`: JIRA parsing logic
- `planner_node.py`: Plan creation logic
- `execution_node.py`: Execution and analysis logic

### Custom State Fields

Add fields to `AgentState` in `agent_state.py`:

```python
class AgentState(TypedDict):
    # ... existing fields ...
    custom_data: Dict[str, Any]
```

## 📚 API Reference

### BugReproductionAgent

Main orchestrator class.

**Methods:**
- `reproduce_bug(issue_key: str, code_files: Dict[str, str] = None) -> Dict[str, Any]`
  - Reproduces bug from JIRA issue
  - Returns final state with results

- `get_workflow_diagram() -> str`
  - Returns ASCII workflow diagram

### JiraParserNode

Fetches and parses JIRA issues.

**Methods:**
- `fetch_jira_issue(issue_key: str) -> Dict[str, Any]`
- `parse_with_claude(raw_issue: Dict) -> JiraIssueDetails`

### ReproductionPlannerNode

Creates reproduction plans.

**Methods:**
- `create_reproduction_plan(issue_details: JiraIssueDetails, code_files: Dict = None) -> ReproductionPlan`
- `validate_plan(plan: ReproductionPlan) -> List[str]`

### ExecutionNode

Executes and analyzes reproduction.

**Methods:**
- `simulate_step_execution(step: ReproductionStep, context: Dict) -> ReproductionStep`
- `analyze_reproduction_results(plan: ReproductionPlan, executed_steps: List, context: Dict) -> ReproductionResult`

## 🤝 Contributing

This is a proof-of-concept project. Feel free to:
- Fork and modify for your needs
- Add new features
- Improve prompts
- Add real browser automation (Selenium, Playwright)

## 📄 License

Educational/POC project. Modify as needed.

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [Claude Sonnet 4.0](https://www.anthropic.com/claude)
- UI with [Rich](https://github.com/Textualize/rich)

---

**Made with ❤️ using Claude AI**
