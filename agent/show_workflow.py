"""
Display the Bug Reproduction Agent workflow diagram
"""
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def show_workflow():
    """Display the complete workflow diagram"""
    
    workflow = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                   BUG REPRODUCTION AGENT WORKFLOW                  ┃
┃                    Powered by Claude Sonnet 4.0                    ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

                              ┌──────────────┐
                              │  User Input  │
                              │  (Issue Key) │
                              └──────┬───────┘
                                     │
                                     ▼
            ╔════════════════════════════════════════════╗
            ║         NODE 1: JIRA PARSER                ║
            ║  ┌──────────────────────────────────────┐ ║
            ║  │  1. Fetch issue from JIRA API        │ ║
            ║  │  2. Send to Claude Sonnet 4.0        │ ║
            ║  │  3. Extract:                         │ ║
            ║  │     • Reproduction steps             │ ║
            ║  │     • Expected behavior              │ ║
            ║  │     • Actual behavior                │ ║
            ║  │     • Application details            │ ║
            ║  └──────────────────────────────────────┘ ║
            ║                                            ║
            ║  Output: JiraIssueDetails                 ║
            ╚════════════════════════════════════════════╝
                                     │
                                     ▼
            ╔════════════════════════════════════════════╗
            ║      NODE 2: REPRODUCTION PLANNER          ║
            ║  ┌──────────────────────────────────────┐ ║
            ║  │  1. Analyze issue details            │ ║
            ║  │  2. Consider code context (if any)   │ ║
            ║  │  3. Send to Claude Sonnet 4.0        │ ║
            ║  │  4. Generate:                        │ ║
            ║  │     • Prerequisites                  │ ║
            ║  │     • Environment setup              │ ║
            ║  │     • Atomic steps with actions      │ ║
            ║  │     • Verification checkpoints       │ ║
            ║  │  5. Validate plan completeness       │ ║
            ║  └──────────────────────────────────────┘ ║
            ║                                            ║
            ║  Output: ReproductionPlan                 ║
            ╚════════════════════════════════════════════╝
                                     │
                                     ▼
            ╔════════════════════════════════════════════╗
            ║        NODE 3: EXECUTION ENGINE            ║
            ║  ┌──────────────────────────────────────┐ ║
            ║  │  For each step in plan:              │ ║
            ║  │  ┌────────────────────────────────┐  │ ║
            ║  │  │ 1. Prepare context             │  │ ║
            ║  │  │ 2. Send to Claude (simulate)   │  │ ║
            ║  │  │ 3. Capture result:             │  │ ║
            ║  │  │    • Status (success/failed)   │  │ ║
            ║  │  │    • Actual outcome            │  │ ║
            ║  │  │    • Error (if any)            │  │ ║
            ║  │  │ 4. Update context              │  │ ║
            ║  │  └────────────────────────────────┘  │ ║
            ║  │                                      │ ║
            ║  │  After all steps:                   │ ║
            ║  │  • Send results to Claude           │ ║
            ║  │  • Perform root cause analysis      │ ║
            ║  │  • Generate recommendations         │ ║
            ║  │  • Calculate confidence score       │ ║
            ║  └──────────────────────────────────────┘ ║
            ║                                            ║
            ║  Output: ReproductionResult               ║
            ╚════════════════════════════════════════════╝
                                     │
                                     ▼
            ╔════════════════════════════════════════════╗
            ║         NODE 4: REPORT GENERATOR           ║
            ║  ┌──────────────────────────────────────┐ ║
            ║  │  1. Format final report              │ ║
            ║  │     • Summary                        │ ║
            ║  │     • Detailed steps                 │ ║
            ║  │     • Root cause                     │ ║
            ║  │     • Recommendations                │ ║
            ║  │  2. Save to JSON file                │ ║
            ║  │  3. Post to JIRA (if enabled)        │ ║
            ║  │  4. Display in CLI                   │ ║
            ║  └──────────────────────────────────────┘ ║
            ╚════════════════════════════════════════════╝
                                     │
                                     ▼
                              ┌──────────────┐
                              │ Final Report │
                              │  & Results   │
                              └──────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                         STATE MANAGEMENT (LangGraph)

┌─────────────────────────────────────────────────────────────────┐
│  AgentState (TypedDict)                                          │
│  ├─ jira_issue_key: str                                         │
│  ├─ raw_jira_data: Dict                                         │
│  ├─ parsed_issue: JiraIssueDetails                              │
│  ├─ reproduction_plan: ReproductionPlan                         │
│  ├─ current_step: int                                           │
│  ├─ reproduction_result: ReproductionResult                     │
│  ├─ messages: List[str]                                         │
│  ├─ errors: List[str]                                           │
│  ├─ status: str (fetching → parsing → planning → executing →   │
│  │              analyzing → completed)                          │
│  └─ code_files: Dict[str, str]                                  │
└─────────────────────────────────────────────────────────────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                            ERROR HANDLING

                    ┌─────────────────────────┐
                    │   Conditional Routing   │
                    └───────────┬─────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
                ▼               ▼               ▼
         ┌──────────┐    ┌──────────┐    ┌──────────┐
         │ Success  │    │  Retry   │    │  Abort   │
         │   Path   │    │   Path   │    │   Path   │
         └──────────┘    └──────────┘    └──────────┘

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

                         KEY TECHNOLOGIES

    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
    │  LangGraph   │    │   Claude     │    │   Pydantic   │
    │  Workflow    │───▶│  Sonnet 4.0  │───▶│   Models     │
    │ Orchestrator │    │      AI      │    │  Validation  │
    └──────────────┘    └──────────────┘    └──────────────┘
           │                    │                    │
           └────────────────────┴────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │    Structured Output   │
                    │  • Type-safe          │
                    │  • Validated          │
                    │  • JSON serializable  │
                    └───────────────────────┘
"""
    
    console.print(workflow, style="cyan")


def show_data_models():
    """Display data model structure"""
    
    models = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                        DATA MODELS (Pydantic)                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌─────────────────────────────────────────────────────────────────┐
│  JiraIssueDetails                                                │
│  ├─ issue_key: str                                              │
│  ├─ summary: str                                                │
│  ├─ description: Optional[str]                                  │
│  ├─ issue_type: str                                             │
│  ├─ status: str                                                 │
│  ├─ reproduction_steps: List[str]                               │
│  ├─ expected_behavior: Optional[str]                            │
│  ├─ actual_behavior: Optional[str]                              │
│  └─ application_details: ApplicationDetails                     │
│       ├─ name: Optional[str]                                    │
│       ├─ version: Optional[str]                                 │
│       ├─ environment: Optional[str]                             │
│       ├─ url: Optional[str]                                     │
│       └─ platform: Optional[str]                                │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ReproductionPlan                                                │
│  ├─ issue_key: str                                              │
│  ├─ reproduction_steps: List[ReproductionStep]                  │
│  │    ├─ step_number: int                                       │
│  │    ├─ description: str                                       │
│  │    ├─ action: str (navigate|click|input|verify|execute)     │
│  │    ├─ target: Optional[str]                                  │
│  │    ├─ expected_result: Optional[str]                         │
│  │    ├─ actual_result: Optional[str]                           │
│  │    ├─ status: str (pending|success|failed|skipped)          │
│  │    └─ error: Optional[str]                                   │
│  ├─ prerequisites: List[str]                                    │
│  ├─ environment_setup: Dict[str, Any]                           │
│  └─ expected_outcome: str                                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ReproductionResult                                              │
│  ├─ issue_key: str                                              │
│  ├─ bug_reproduced: bool                                        │
│  ├─ executed_steps: List[ReproductionStep]                      │
│  ├─ screenshots: List[str]                                      │
│  ├─ logs: List[str]                                             │
│  ├─ root_cause_analysis: Optional[str]                          │
│  ├─ recommendations: List[str]                                  │
│  └─ confidence_score: float (0.0 - 1.0)                         │
└─────────────────────────────────────────────────────────────────┘
"""
    
    console.print(models, style="green")


def show_usage():
    """Display usage examples"""
    
    usage = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                           USAGE EXAMPLES                           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

1. BASIC REPRODUCTION
   ┌────────────────────────────────────────────────────────────┐
   │ python reproduce_bug_cli.py KAN-4                          │
   └────────────────────────────────────────────────────────────┘

2. WITH CODE CONTEXT
   ┌────────────────────────────────────────────────────────────┐
   │ python reproduce_bug_cli.py KAN-4 --code app.py utils.py  │
   └────────────────────────────────────────────────────────────┘

3. VERBOSE MODE
   ┌────────────────────────────────────────────────────────────┐
   │ python reproduce_bug_cli.py KAN-4 --verbose                │
   └────────────────────────────────────────────────────────────┘

4. INTERACTIVE MODE
   ┌────────────────────────────────────────────────────────────┐
   │ python reproduce_bug_cli.py --interactive                  │
   │ > KAN-4                                                    │
   │ > KAN-5                                                    │
   │ > exit                                                     │
   └────────────────────────────────────────────────────────────┘

5. PROGRAMMATIC
   ┌────────────────────────────────────────────────────────────┐
   │ from bug_reproduction_agent import BugReproductionAgent    │
   │                                                            │
   │ agent = BugReproductionAgent()                             │
   │ result = agent.reproduce_bug("KAN-4")                      │
   │                                                            │
   │ if result["reproduction_result"]["bug_reproduced"]:       │
   │     print("Bug confirmed!")                                │
   └────────────────────────────────────────────────────────────┘
"""
    
    console.print(usage, style="yellow")


def main():
    """Display all diagrams"""
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold cyan]Bug Reproduction Agent - Workflow Visualization[/bold cyan]",
        border_style="cyan"
    ))
    
    show_workflow()
    
    console.print("\n")
    show_data_models()
    
    console.print("\n")
    show_usage()
    
    console.print("\n")
    console.print(Panel.fit(
        "[bold green]For more details, see:[/bold green]\n"
        "• QUICKSTART.md - Quick start guide\n"
        "• AGENT_GUIDE.md - Complete documentation\n"
        "• ARCHITECTURE.md - Architecture details\n"
        "• SUMMARY.md - Project summary",
        border_style="green"
    ))


if __name__ == "__main__":
    main()
