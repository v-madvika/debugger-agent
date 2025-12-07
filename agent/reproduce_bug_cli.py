import logging
import sys

# Configure logging FIRST, before other imports
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)8s] %(name)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # Explicitly use stdout
        logging.FileHandler('bug_reproduction.log', mode='w')  # Overwrite log file
    ],
    force=True  # Force reconfiguration
)

# Set all loggers to DEBUG
logging.getLogger().setLevel(logging.DEBUG)

# Enable logging for specific modules
logging.getLogger('agent.jira_parser').setLevel(logging.DEBUG)
logging.getLogger('agent.jira_parser_node').setLevel(logging.DEBUG)
logging.getLogger('agent.bug_reproduction_agent').setLevel(logging.DEBUG)

"""
CLI for Bug Reproduction Agent
Enhanced command-line interface with rich formatting
"""
import argparse
import sys
from pathlib import Path
from typing import Dict, Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.markdown import Markdown
from bug_reproduction_agent import BugReproductionAgent
import json
import os

console = Console()


class BugReproductionCLI:
    """Enhanced CLI for bug reproduction agent"""
    
    def __init__(self):
        self.agent = BugReproductionAgent()
    
    def load_code_files(self, file_paths: list) -> Dict[str, str]:
        """Load code files from paths"""
        code_files = {}
        
        for file_path in file_paths:
            path = Path(file_path)
            if not path.exists():
                console.print(f"[yellow]⚠ Warning: File not found: {file_path}[/yellow]")
                continue
            
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    code_files[path.name] = f.read()
                console.print(f"[green]✓[/green] Loaded: {path.name}")
            except Exception as e:
                console.print(f"[red]✗[/red] Failed to load {path.name}: {str(e)}")
        
        return code_files
    
    def run_reproduction(
        self, 
        issue_key: str, 
        code_files: Optional[Dict[str, str]] = None,
        verbose: bool = False
    ):
        """Run bug reproduction with rich output"""
        console.print("Starting reproduction process...1")
        
        # Header
        console.print(Panel(
            f"[bold cyan]🤖 Bug Reproduction Agent[/bold cyan]\n"
            f"Issue: [bold]{issue_key}[/bold]\n"
            f"LLM: Claude Sonnet 4.0",
            border_style="cyan"
        ))
        
        # Show workflow
        if verbose:
            console.print("\n[bold]Workflow:[/bold]")
            console.print(self.agent.get_workflow_diagram())
        
        # Run with progress indicator
        console.print("\n[bold cyan]Starting reproduction workflow...[/bold cyan]\n")
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("[cyan]Running agent...", total=None)

                print("Starting reproduction process...2")
                
                result = self.agent.reproduce_bug(issue_key, code_files)

                print(" reproduction process completed, preparing report...")
                
                progress.update(task, completed=True)

                print(" update completed...")

            
            # Display results
            try:
                print("About to display results...")
                self._display_results(result, verbose)
                print("Display results completed successfully...")
            except Exception as e:
                console.print(f"\n[bold red]❌ Error displaying results:[/bold red] {str(e)}")
                logging.error(f"Error in _display_results: {str(e)}", exc_info=True)
                if verbose:
                    import traceback
                    console.print(f"\n[red]{traceback.format_exc()}[/red]")
            
            # Save results
            self._save_results(result, issue_key)
            
            return result
            
        except Exception as e:
            console.print(f"\n[bold red]❌ Error:[/bold red] {str(e)}")
            if verbose:
                import traceback
                console.print(f"\n[red]{traceback.format_exc()}[/red]")
            sys.exit(1)
    
    def _display_results(self, result: Dict, verbose: bool):
        """Display results with rich formatting"""

        try:
            print("Displaying results started...")
            
            # Status
            status = result.get("status", "unknown")
            status_color = "green" if status == "completed" else "red"
            console.print(f"\n[bold {status_color}]Status: {status.upper()}[/bold {status_color}]")
            
            # Messages
            if verbose:
                console.print("\n[bold]Execution Log:[/bold]")
                for msg in result.get("messages", []):
                    console.print(f"  {msg}")
            
            # Errors
            if result.get("errors"):
                console.print("\n[bold red]Errors:[/bold red]")
                for error in result["errors"]:
                    console.print(f"  [red]•[/red] {error}")
            
            # Reproduction Result
            print("About to display reproduction result...")
            repro_result = result.get("reproduction_result")
            if repro_result:
                self._display_reproduction_result(repro_result)
            else:
                print("No reproduction_result found in result")
                logging.warning("No reproduction_result found in result dictionary")
            
            print("_display_results completed successfully")
        except Exception as e:
            print(f"Exception in _display_results: {str(e)}")
            logging.error(f"Exception in _display_results: {str(e)}", exc_info=True)
            raise
    
    def _display_reproduction_result(self, result: Dict):
        """Display reproduction result in a formatted table"""
        try:
            print("Displaying results in a formatted table...")
            
            console.print("\n" + "="*70)
            console.print("[bold cyan]REPRODUCTION RESULT[/bold cyan]")
            console.print("="*70)
            
            # Summary table
            table = Table(show_header=False, box=None)
            table.add_column("Field", style="cyan")
            table.add_column("Value")
            
            bug_reproduced = result.get("bug_reproduced", False)
            status_icon = "✓" if bug_reproduced else "✗"
            status_color = "green" if bug_reproduced else "red"
            
            table.add_row(
                "Bug Reproduced",
                f"[{status_color}]{status_icon} {'YES' if bug_reproduced else 'NO'}[/{status_color}]"
            )
            table.add_row(
                "Confidence Score",
                f"{result.get('confidence_score', 0):.0%}"
            )
            table.add_row(
                "Steps Executed",
                str(len(result.get("executed_steps", [])))
            )
            
            console.print(table)
            
            # Root Cause Analysis
            console.print("\n[bold]Root Cause Analysis:[/bold]")
            console.print(f"  {result.get('root_cause_analysis', 'N/A')}")
            
            # Recommendations
            console.print("\n[bold]Recommendations:[/bold]")
            for i, rec in enumerate(result.get("recommendations", []), 1):
                console.print(f"  {i}. {rec}")
            
            # Detailed Steps
            if result.get("executed_steps"):
                console.print("\n[bold]Execution Steps:[/bold]")
                
                steps_table = Table()
                steps_table.add_column("Step", style="cyan", width=6)
                steps_table.add_column("Action", style="yellow", width=12)
                steps_table.add_column("Status", width=10)
                steps_table.add_column("Description", width=40)
                
                for step in result["executed_steps"]:
                    status = step.get("status", "unknown")
                    status_icon = "✓" if status == "success" else "✗" if status == "failed" else "⊙"
                    status_color = "green" if status == "success" else "red" if status == "failed" else "yellow"
                    
                    steps_table.add_row(
                        str(step.get("step_number", "?")),
                        step.get("action", "").upper(),
                        f"[{status_color}]{status_icon} {status}[/{status_color}]",
                        step.get("description", "")[:40] + "..."
                    )
                
                console.print(steps_table)
            
            console.print("="*70)
            
            print("_display_reproduction_result completed successfully")
        except Exception as e:
            print(f"Exception in _display_reproduction_result: {str(e)}")
            logging.error(f"Exception in _display_reproduction_result: {str(e)}", exc_info=True)
            raise
    
    def _save_results(self, result: Dict, issue_key: str):
        """Save results to file"""

        print("Saving results started...")
        
        # Create results directory
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        # Save JSON
        output_file = results_dir / f"{issue_key}_result.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        
        console.print(f"\n[green]✓[/green] Results saved to: {output_file}")
    
    def interactive_mode(self):
        """Interactive mode for testing multiple issues"""
        
        console.print(Panel(
            "[bold cyan]🤖 Bug Reproduction Agent - Interactive Mode[/bold cyan]\n"
            "Type 'help' for commands, 'exit' to quit",
            border_style="cyan"
        ))
        
        while True:
            try:
                command = console.input("\n[cyan]>[/cyan] ").strip()
                
                if not command:
                    continue
                
                if command.lower() in ['exit', 'quit', 'q']:
                    console.print("[yellow]Goodbye![/yellow]")
                    break
                
                if command.lower() == 'help':
                    self._show_help()
                    continue
                
                if command.lower() == 'workflow':
                    console.print(self.agent.get_workflow_diagram())
                    continue
                
                # Assume it's an issue key
                if '-' in command:
                    self.run_reproduction(command, verbose=True)
                else:
                    console.print("[yellow]Invalid command. Type 'help' for usage.[/yellow]")
                
            except KeyboardInterrupt:
                console.print("\n[yellow]Interrupted. Type 'exit' to quit.[/yellow]")
            except Exception as e:
                console.print(f"[red]Error: {str(e)}[/red]")
    
    def _show_help(self):
        """Show help message"""
        help_text = """
[bold]Available Commands:[/bold]

  [cyan]<ISSUE-KEY>[/cyan]     Reproduce bug from JIRA issue (e.g., KAN-4)
  [cyan]workflow[/cyan]        Show workflow diagram
  [cyan]help[/cyan]            Show this help message
  [cyan]exit[/cyan]            Exit interactive mode

[bold]Examples:[/bold]
  > KAN-4
  > PROJ-123
"""
        console.print(help_text)


def main():
    """Main CLI entry point"""
    
    parser = argparse.ArgumentParser(
        description="AI-powered Bug Reproduction Agent with LangGraph",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reproduce a bug from JIRA
  python reproduce_bug_cli.py KAN-4
  
  # Include code files for context
  python reproduce_bug_cli.py KAN-4 --code app.py utils.py
  
  # Interactive mode
  python reproduce_bug_cli.py --interactive
  
  # Verbose output
  python reproduce_bug_cli.py KAN-4 --verbose
        """
    )
    
    parser.add_argument(
        "issue_key",
        nargs="?",
        help="JIRA issue key (e.g., KAN-4)"
    )
    
    parser.add_argument(
        "--code",
        nargs="+",
        help="Code files to include for context"
    )
    
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive mode"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed execution logs"
    )
    
    parser.add_argument(
        "--workflow",
        action="store_true",
        help="Show workflow diagram and exit"
    )
    
    args = parser.parse_args()
    
    # Create CLI
    cli = BugReproductionCLI()
    
    # Show workflow
    if args.workflow:
        console.print(cli.agent.get_workflow_diagram())
        sys.exit(0)
    
    # Interactive mode
    if args.interactive:
        cli.interactive_mode()
        sys.exit(0)
    
    # Require issue key for non-interactive mode
    if not args.issue_key:
        parser.print_help()
        sys.exit(1)
    
    # Load code files
    code_files = None
    if args.code:
        console.print("[cyan]Loading code files...[/cyan]")
        code_files = cli.load_code_files(args.code)
        console.print()
    
    # Run reproduction
    cli.run_reproduction(args.issue_key, code_files, args.verbose)


if __name__ == "__main__":
    main()
