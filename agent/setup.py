"""
Complete Installation and Setup Script
Automates the setup process for Bug Reproduction Agent
"""
import subprocess
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import os

console = Console()


def check_python_version():
    """Check if Python version is 3.9+"""
    console.print("\n[cyan]Checking Python version...[/cyan]")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        console.print(f"[red]✗ Python 3.9+ required. You have {version.major}.{version.minor}[/red]")
        return False
    
    console.print(f"[green]✓ Python {version.major}.{version.minor}.{version.micro}[/green]")
    return True


def install_dependencies():
    """Install required packages"""
    console.print("\n[cyan]Installing dependencies...[/cyan]")
    
    requirements_file = Path("..") / "requirements.txt"
    
    if not requirements_file.exists():
        console.print("[red]✗ requirements.txt not found[/red]")
        return False
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Installing packages...", total=None)
            
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--quiet"],
                capture_output=True,
                text=True
            )
            
            progress.update(task, completed=True)
        
        if result.returncode == 0:
            console.print("[green]✓ Dependencies installed successfully[/green]")
            return True
        else:
            console.print(f"[red]✗ Installation failed:[/red]")
            console.print(result.stderr)
            return False
            
    except Exception as e:
        console.print(f"[red]✗ Error installing dependencies: {str(e)}[/red]")
        return False


def setup_env_file():
    """Create .env file from template"""
    console.print("\n[cyan]Setting up environment file...[/cyan]")
    
    env_file = Path(".env")
    example_file = Path(".env.example")
    
    if env_file.exists():
        console.print("[yellow]⚠ .env file already exists[/yellow]")
        response = console.input("  Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            console.print("[yellow]Keeping existing .env file[/yellow]")
            return True
    
    if not example_file.exists():
        console.print("[red]✗ .env.example not found[/red]")
        return False
    
    try:
        # Copy template
        with open(example_file, 'r') as src:
            content = src.read()
        
        with open(env_file, 'w') as dst:
            dst.write(content)
        
        console.print("[green]✓ Created .env file from template[/green]")
        console.print("\n[bold yellow]IMPORTANT:[/bold yellow]")
        console.print("  Edit .env and add your actual API keys:")
        console.print("  1. ANTHROPIC_API_KEY")
        console.print("  2. JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN")
        console.print("  3. JIRA_PROJECT_KEY")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error creating .env file: {str(e)}[/red]")
        return False


def verify_imports():
    """Verify all required packages can be imported"""
    console.print("\n[cyan]Verifying package imports...[/cyan]")
    
    required_packages = [
        "anthropic",
        "langgraph",
        "langchain",
        "langchain_anthropic",
        "pydantic",
        "requests",
        "rich",
        "dotenv"
    ]
    
    failed = []
    
    for package in required_packages:
        try:
            __import__(package)
            console.print(f"  [green]✓[/green] {package}")
        except ImportError:
            console.print(f"  [red]✗[/red] {package}")
            failed.append(package)
    
    if failed:
        console.print(f"\n[red]✗ Failed to import: {', '.join(failed)}[/red]")
        return False
    
    console.print("[green]✓ All packages imported successfully[/green]")
    return True


def create_directories():
    """Create necessary directories"""
    console.print("\n[cyan]Creating directories...[/cyan]")
    
    dirs = ["results"]
    
    for dir_name in dirs:
        dir_path = Path("..") / dir_name
        dir_path.mkdir(exist_ok=True)
        console.print(f"  [green]✓[/green] {dir_name}/")
    
    return True


def show_next_steps():
    """Display next steps for the user"""
    
    next_steps = """
[bold cyan]🎉 Setup Complete![/bold cyan]

[bold]Next Steps:[/bold]

1. [yellow]Configure API Keys[/yellow]
   Edit .env and add your actual credentials:
   • ANTHROPIC_API_KEY (from console.anthropic.com)
   • JIRA credentials (URL, email, API token)
   • JIRA_PROJECT_KEY

2. [yellow]Verify Setup[/yellow]
   cd agent
   python test_setup.py

3. [yellow]View Workflow[/yellow]
   python show_workflow.py

4. [yellow]Run Examples[/yellow]
   python examples.py

5. [yellow]Reproduce Your First Bug[/yellow]
   python reproduce_bug_cli.py KAN-4

[bold]Documentation:[/bold]
• QUICKSTART.md  - Quick start guide
• AGENT_GUIDE.md - Complete documentation
• ARCHITECTURE.md - Architecture details

[bold]Need Help?[/bold]
Run: python test_setup.py
"""
    
    console.print(Panel(next_steps, border_style="green"))


def main():
    """Run complete setup"""
    
    console.print(Panel.fit(
        "[bold cyan]Bug Reproduction Agent - Setup Script[/bold cyan]\n"
        "This script will install and configure everything you need",
        border_style="cyan"
    ))
    
    steps = []
    
    # Step 1: Check Python version
    steps.append(("Python Version", check_python_version()))
    
    if not steps[-1][1]:
        console.print("\n[red]Setup failed. Please install Python 3.9 or higher.[/red]")
        sys.exit(1)
    
    # Step 2: Install dependencies
    steps.append(("Install Dependencies", install_dependencies()))
    
    # Step 3: Verify imports
    steps.append(("Verify Imports", verify_imports()))
    
    # Step 4: Setup .env
    steps.append(("Setup .env File", setup_env_file()))
    
    # Step 5: Create directories
    steps.append(("Create Directories", create_directories()))
    
    # Summary
    console.print("\n" + "="*70)
    console.print("[bold]SETUP SUMMARY[/bold]")
    console.print("="*70)
    
    all_passed = True
    for step_name, passed in steps:
        status = "[green]✓ PASSED[/green]" if passed else "[red]✗ FAILED[/red]"
        console.print(f"{step_name:.<50} {status}")
        if not passed:
            all_passed = False
    
    console.print("="*70)
    
    if all_passed:
        show_next_steps()
    else:
        console.print("\n[red]⚠ Setup incomplete. Please fix the errors above.[/red]")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]Setup interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {str(e)}[/red]")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1)
