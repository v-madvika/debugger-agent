"""
Quick test to read KAN-4 from Jira
"""
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from jira_client import SimpleJiraClient

load_dotenv()
console = Console()

def test_kan4():
    console.print(Panel(
        "[bold cyan]Testing KAN-4 Ticket Retrieval[/bold cyan]",
        border_style="cyan"
    ))
    
    try:
        # Create Jira client
        jira = SimpleJiraClient()
        
        # Get KAN-4
        console.print("\n[yellow]Fetching KAN-4...[/yellow]")
        issue = jira.get_issue("KAN-4")
        
        # Extract fields
        fields = issue.get('fields', {})
        
        # Display the ticket
        ticket_info = f"""
# Jira Ticket: {issue.get('key')}

**Summary:** {fields.get('summary')}

**Description:**
{fields.get('description', 'No description provided')}

**Details:**
- **Type:** {fields.get('issuetype', {}).get('name')}
- **Status:** {fields.get('status', {}).get('name')}
- **Priority:** {fields.get('priority', {}).get('name', 'None')}
- **Assignee:** {fields.get('assignee', {}).get('displayName', 'Unassigned')}
- **Reporter:** {fields.get('reporter', {}).get('displayName', 'Unknown')}
- **Created:** {fields.get('created', 'Unknown')}
"""
        
        console.print(Panel(
            Markdown(ticket_info),
            title="[bold green]✅ Successfully Retrieved KAN-4[/bold green]",
            border_style="green"
        ))
        
        # Show raw JSON (optional)
        console.print("\n[cyan]Raw JSON available in 'issue' variable if needed[/cyan]")
        
        return issue
        
    except Exception as e:
        console.print(Panel(
            f"[bold red]Error: {str(e)}[/bold red]",
            title="❌ Failed to Retrieve KAN-4",
            border_style="red"
        ))
        raise

if __name__ == "__main__":
    issue = test_kan4()
    
    console.print("\n[bold cyan]Test completed! The agent can read Jira tickets.[/bold cyan]")
