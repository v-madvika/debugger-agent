"""
Example: Complete Bug Reproduction Workflow
Demonstrates all features of the Bug Reproduction Agent
"""
from bug_reproduction_agent import BugReproductionAgent
from rich.console import Console
from rich.panel import Panel
import json

console = Console()


def example_1_basic_reproduction():
    """Example 1: Basic bug reproduction"""
    console.print(Panel(
        "[bold cyan]Example 1: Basic Bug Reproduction[/bold cyan]",
        border_style="cyan"
    ))
    
    # Initialize agent
    agent = BugReproductionAgent()
    
    # Reproduce bug
    console.print("\n[yellow]Reproducing bug from JIRA issue KAN-4...[/yellow]")
    result = agent.reproduce_bug("KAN-4")
    
    # Check status
    if result["status"] == "completed":
        console.print("[green]✓ Reproduction completed successfully![/green]")
        
        # Access results
        repro_result = result["reproduction_result"]
        console.print(f"\nBug reproduced: {repro_result['bug_reproduced']}")
        console.print(f"Confidence: {repro_result['confidence_score']:.0%}")
    else:
        console.print("[red]✗ Reproduction failed[/red]")
        for error in result.get("errors", []):
            console.print(f"  Error: {error}")


def example_2_with_code_context():
    """Example 2: Bug reproduction with code context"""
    console.print(Panel(
        "[bold cyan]Example 2: Bug Reproduction with Code Context[/bold cyan]",
        border_style="cyan"
    ))
    
    # Load code files
    code_files = {
        "app.py": """
def process_user_data(user):
    # Bug: No null check
    return user.name.upper()
""",
        "utils.py": """
def get_user(user_id):
    if user_id < 0:
        return None  # Bug: Returns None without warning
    return {"name": "John", "id": user_id}
"""
    }
    
    console.print(f"\n[yellow]Including {len(code_files)} code files for context[/yellow]")
    
    # Initialize agent
    agent = BugReproductionAgent()
    
    # Reproduce with code context
    result = agent.reproduce_bug("KAN-4", code_files=code_files)
    
    # Show root cause analysis
    if result["status"] == "completed":
        repro_result = result["reproduction_result"]
        console.print("\n[bold]Root Cause Analysis:[/bold]")
        console.print(repro_result["root_cause_analysis"])
        
        console.print("\n[bold]Recommendations:[/bold]")
        for i, rec in enumerate(repro_result["recommendations"], 1):
            console.print(f"  {i}. {rec}")


def example_3_analyze_results():
    """Example 3: Detailed result analysis"""
    console.print(Panel(
        "[bold cyan]Example 3: Detailed Result Analysis[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = BugReproductionAgent()
    result = agent.reproduce_bug("KAN-4")
    
    if result["status"] != "completed":
        console.print("[red]Reproduction not completed[/red]")
        return
    
    repro_result = result["reproduction_result"]
    
    # Analyze each step
    console.print("\n[bold]Step-by-Step Analysis:[/bold]")
    for step in repro_result["executed_steps"]:
        status_color = "green" if step["status"] == "success" else "red"
        console.print(f"\n[cyan]Step {step['step_number']}:[/cyan] {step['description']}")
        console.print(f"  Action: {step['action']}")
        console.print(f"  Status: [{status_color}]{step['status']}[/{status_color}]")
        console.print(f"  Expected: {step['expected_result']}")
        console.print(f"  Actual: {step['actual_result']}")
        
        if step.get("error"):
            console.print(f"  [red]Error: {step['error']}[/red]")


def example_4_workflow_state():
    """Example 4: Inspecting workflow state"""
    console.print(Panel(
        "[bold cyan]Example 4: Inspecting Workflow State[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = BugReproductionAgent()
    result = agent.reproduce_bug("KAN-4")
    
    # Show parsed JIRA issue
    console.print("\n[bold]Parsed JIRA Issue:[/bold]")
    parsed_issue = result.get("parsed_issue", {})
    console.print(f"  Key: {parsed_issue.get('issue_key', 'N/A')}")
    console.print(f"  Summary: {parsed_issue.get('summary', 'N/A')}")
    console.print(f"  Type: {parsed_issue.get('issue_type', 'N/A')}")
    console.print(f"  Status: {parsed_issue.get('status', 'N/A')}")
    
    # Show application details
    app_details = parsed_issue.get("application_details", {})
    if app_details:
        console.print("\n[bold]Application Details:[/bold]")
        console.print(f"  Name: {app_details.get('name', 'N/A')}")
        console.print(f"  Version: {app_details.get('version', 'N/A')}")
        console.print(f"  Environment: {app_details.get('environment', 'N/A')}")
        console.print(f"  Platform: {app_details.get('platform', 'N/A')}")
    
    # Show reproduction plan
    plan = result.get("reproduction_plan", {})
    if plan:
        console.print("\n[bold]Reproduction Plan:[/bold]")
        console.print(f"  Steps: {len(plan.get('reproduction_steps', []))}")
        console.print(f"  Prerequisites: {len(plan.get('prerequisites', []))}")
        
        # Show prerequisites
        prereqs = plan.get("prerequisites", [])
        if prereqs:
            console.print("\n  [cyan]Prerequisites:[/cyan]")
            for prereq in prereqs:
                console.print(f"    - {prereq}")


def example_5_batch_processing():
    """Example 5: Batch processing multiple issues"""
    console.print(Panel(
        "[bold cyan]Example 5: Batch Processing[/bold cyan]",
        border_style="cyan"
    ))
    
    # List of issues to process
    issue_keys = ["KAN-4", "KAN-5", "KAN-6"]
    
    agent = BugReproductionAgent()
    results = []
    
    for issue_key in issue_keys:
        console.print(f"\n[yellow]Processing {issue_key}...[/yellow]")
        
        try:
            result = agent.reproduce_bug(issue_key)
            results.append({
                "issue_key": issue_key,
                "status": result["status"],
                "bug_reproduced": result.get("reproduction_result", {}).get("bug_reproduced", False)
            })
            
            console.print(f"[green]✓ {issue_key} completed[/green]")
        except Exception as e:
            console.print(f"[red]✗ {issue_key} failed: {str(e)}[/red]")
            results.append({
                "issue_key": issue_key,
                "status": "failed",
                "error": str(e)
            })
    
    # Summary
    console.print("\n[bold]Batch Processing Summary:[/bold]")
    console.print(json.dumps(results, indent=2))


def example_6_custom_workflow():
    """Example 6: Custom workflow with hooks"""
    console.print(Panel(
        "[bold cyan]Example 6: Custom Workflow Hooks[/bold cyan]",
        border_style="cyan"
    ))
    
    agent = BugReproductionAgent()
    
    # Run with monitoring
    console.print("\n[yellow]Starting monitored reproduction...[/yellow]")
    
    result = agent.reproduce_bug("KAN-4")
    
    # Custom analysis
    if result["status"] == "completed":
        repro_result = result["reproduction_result"]
        
        # Calculate metrics
        total_steps = len(repro_result["executed_steps"])
        successful_steps = sum(
            1 for step in repro_result["executed_steps"] 
            if step["status"] == "success"
        )
        failed_steps = total_steps - successful_steps
        
        console.print("\n[bold]Execution Metrics:[/bold]")
        console.print(f"  Total Steps: {total_steps}")
        console.print(f"  Successful: {successful_steps} ({successful_steps/total_steps:.0%})")
        console.print(f"  Failed: {failed_steps} ({failed_steps/total_steps:.0%})")
        console.print(f"  Bug Reproduced: {repro_result['bug_reproduced']}")
        console.print(f"  Confidence: {repro_result['confidence_score']:.0%}")
        
        # Categorize recommendations
        recommendations = repro_result["recommendations"]
        console.print(f"\n[bold]Recommendations ({len(recommendations)}):[/bold]")
        for i, rec in enumerate(recommendations, 1):
            # Simple categorization
            if any(word in rec.lower() for word in ["test", "unit", "coverage"]):
                category = "🧪 Testing"
            elif any(word in rec.lower() for word in ["fix", "patch", "correct"]):
                category = "🔧 Fix"
            elif any(word in rec.lower() for word in ["refactor", "improve", "optimize"]):
                category = "♻️  Refactor"
            else:
                category = "📝 General"
            
            console.print(f"  {category}: {rec}")


def main():
    """Run all examples"""
    console.print("[bold green]Bug Reproduction Agent - Examples[/bold green]\n")
    
    examples = [
        ("Basic Reproduction", example_1_basic_reproduction),
        ("With Code Context", example_2_with_code_context),
        ("Analyze Results", example_3_analyze_results),
        ("Workflow State", example_4_workflow_state),
        ("Batch Processing", example_5_batch_processing),
        ("Custom Workflow", example_6_custom_workflow),
    ]
    
    console.print("Available examples:")
    for i, (name, _) in enumerate(examples, 1):
        console.print(f"  {i}. {name}")
    
    console.print("\nSelect example (1-6) or 'all': ", end="")
    
    try:
        choice = input().strip()
        
        if choice.lower() == "all":
            for name, func in examples:
                console.print(f"\n{'='*70}\n")
                func()
                console.print("\n" + "="*70)
        elif choice.isdigit() and 1 <= int(choice) <= len(examples):
            name, func = examples[int(choice) - 1]
            func()
        else:
            console.print("[red]Invalid choice[/red]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")


if __name__ == "__main__":
    main()
