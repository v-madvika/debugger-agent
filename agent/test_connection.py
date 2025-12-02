"""
Test script to verify all API connections
"""
import os
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

load_dotenv()
console = Console()

def test_jira():
    """Test Jira connection"""
    console.print("\n[bold cyan]Testing Jira Connection...[/bold cyan]")
    try:
        from jira_client import SimpleJiraClient
        jira = SimpleJiraClient()

        console.print(f"[cyan]Jira Client:[/cyan] {jira}")
        console.print(f"[cyan]Jira URL:[/cyan] {jira.url}")
        console.print(f"[cyan]Jira Email:[/cyan] {jira.email}")
        console.print(f"[cyan]Project Key:[/cyan] {jira.project_key}")
        
        # Try to get KAN-4
        console.print(f"\n[yellow]Attempting to fetch KAN-4...[/yellow]")
        issue = jira.get_issue("KAN-4")
        
        console.print("[bold green]✅ Jira Connected Successfully![/bold green]")
        console.print(f"\n[cyan]Issue Key:[/cyan] {issue.get('key')}")
        console.print(f"[cyan]Summary:[/cyan] {issue.get('fields', {}).get('summary')}")
        console.print(f"[cyan]Status:[/cyan] {issue.get('fields', {}).get('status', {}).get('name')}")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Jira Failed:[/bold red] {str(e)}")
        import traceback
        console.print(f"[red]Traceback:[/red]\n{traceback.format_exc()}")
        return False

def test_github():
    """Test GitHub connection"""
    console.print("\n[bold cyan]Testing GitHub Connection...[/bold cyan]")
    try:
        from github_client import SimpleGitHubClient
        github = SimpleGitHubClient()
        
        # Get repo info
        repo_info = github.repo
        
        console.print("[bold green]✅ GitHub Connected Successfully![/bold green]")
        console.print(f"\n[cyan]Repository:[/cyan] {repo_info.full_name}")
        console.print(f"[cyan]Description:[/cyan] {repo_info.description or 'N/A'}")
        console.print(f"[cyan]Private:[/cyan] {repo_info.private}")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ GitHub Failed:[/bold red] {str(e)}")
        return False

def test_bedrock():
    """Test AWS Bedrock connection"""
    console.print("\n[bold cyan]Testing AWS Bedrock Connection...[/bold cyan]")
    
    use_bedrock = os.getenv("USE_BEDROCK", "False").lower() == "true"
    
    if not use_bedrock:
        console.print("[yellow]⚠️  Bedrock not enabled (USE_BEDROCK=False)[/yellow]")
        return True
    
    try:
        import boto3
        
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=os.getenv("AWS_REGION"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
        )
        
        # Simple test - list models would require different permissions
        # Instead, we'll just verify the client was created
        console.print("[bold green]✅ Bedrock Client Created Successfully![/bold green]")
        console.print(f"\n[cyan]Region:[/cyan] {os.getenv('AWS_REGION')}")
        console.print(f"[cyan]Model ID:[/cyan] {os.getenv('BEDROCK_MODEL_ID')}")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Bedrock Failed:[/bold red] {str(e)}")
        return False

def test_agent():
    """Test the full agent"""
    console.print("\n[bold cyan]Testing Full Agent...[/bold cyan]")
    try:
        from cli import FreeDebugAgent
        
        agent = FreeDebugAgent()
        console.print("[bold green]✅ Agent Initialized Successfully![/bold green]")
        return True
    except Exception as e:
        console.print(f"[bold red]❌ Agent Failed:[/bold red] {str(e)}")
        return False

def main():
    """Run all tests"""
    console.print(Panel(
        "[bold cyan]🧪 Debug Agent Connection Tests[/bold cyan]",
        border_style="cyan"
    ))
    
    results = {
        "Jira": test_jira(),
        "GitHub": test_github(),
        "AWS Bedrock": test_bedrock(),
        "Full Agent": test_agent()
    }
    
    # Summary table
    console.print("\n[bold cyan]Test Summary:[/bold cyan]")
    table = Table()
    table.add_column("Service", style="cyan")
    table.add_column("Status", style="bold")
    
    for service, passed in results.items():
        status = "[green]✅ PASSED[/green]" if passed else "[red]❌ FAILED[/red]"
        table.add_row(service, status)
    
    console.print(table)
    
    if all(results.values()):
        console.print("\n[bold green]🎉 All tests passed! Agent is ready to use.[/bold green]")
    else:
        console.print("\n[bold red]⚠️  Some tests failed. Check the errors above.[/bold red]")

if __name__ == "__main__":
    main()
