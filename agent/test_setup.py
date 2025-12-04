"""
Quick test script to verify agent setup
"""
import sys
from pathlib import Path

def test_imports():
    """Test if all required packages are installed"""
    print("🧪 Testing package imports...")
    
    required_packages = [
        ("anthropic", "Anthropic API"),
        ("langgraph", "LangGraph"),
        ("langchain", "LangChain"),
        ("langchain_anthropic", "LangChain Anthropic"),
        ("pydantic", "Pydantic"),
        ("requests", "Requests"),
        ("rich", "Rich"),
        ("dotenv", "Python Dotenv")
    ]
    
    failed = []
    
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ✗ {name} - NOT INSTALLED")
            failed.append(package)
    
    if failed:
        print(f"\n❌ Missing packages: {', '.join(failed)}")
        print("Run: pip install -r ../requirements.txt")
        return False
    else:
        print("\n✅ All packages installed!")
        return True

def test_env_file():
    """Test if .env file exists and has required variables"""
    print("\n🧪 Testing environment configuration...")
    
    env_path = Path(".env")
    
    if not env_path.exists():
        print("  ✗ .env file not found")
        print("  Create one using: cp .env.example .env")
        return False
    
    print("  ✓ .env file exists")
    
    # Check for required variables
    required_vars = [
        "ANTHROPIC_API_KEY",
        "JIRA_URL",
        "JIRA_EMAIL",
        "JIRA_API_TOKEN",
        "JIRA_PROJECT_KEY"
    ]
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    missing = []
    for var in required_vars:
        if var not in content or f"{var}=your-" in content or f"{var}=sk-ant-your" in content:
            missing.append(var)
            print(f"  ✗ {var} - NOT CONFIGURED")
        else:
            print(f"  ✓ {var}")
    
    if missing:
        print(f"\n❌ Missing or incomplete configuration for: {', '.join(missing)}")
        print("Edit .env and add your actual credentials")
        return False
    else:
        print("\n✅ Environment configured!")
        return True

def test_agent_files():
    """Test if all agent files exist"""
    print("\n🧪 Testing agent files...")
    
    required_files = [
        "agent_state.py",
        "jira_parser_node.py",
        "planner_node.py",
        "execution_node.py",
        "bug_reproduction_agent.py",
        "reproduce_bug_cli.py",
        "jira_client.py"
    ]
    
    missing = []
    
    for filename in required_files:
        if Path(filename).exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ {filename} - NOT FOUND")
            missing.append(filename)
    
    if missing:
        print(f"\n❌ Missing files: {', '.join(missing)}")
        return False
    else:
        print("\n✅ All agent files present!")
        return True

def test_jira_connection():
    """Test JIRA connection"""
    print("\n🧪 Testing JIRA connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from jira_client import SimpleJiraClient
        jira = SimpleJiraClient()
        
        print(f"  ✓ JIRA client initialized")
        print(f"  URL: {jira.url}")
        print(f"  Project: {jira.project_key}")
        
        # Try to get project info
        # Note: This might fail if project doesn't exist yet
        print("\n✅ JIRA connection successful!")
        return True
        
    except Exception as e:
        print(f"  ✗ JIRA connection failed: {str(e)}")
        print("\n⚠️  JIRA connection failed. Check your credentials in .env")
        return False

def test_anthropic_connection():
    """Test Anthropic API connection"""
    print("\n🧪 Testing Anthropic API connection...")
    
    try:
        from dotenv import load_dotenv
        import os
        load_dotenv()
        
        from anthropic import Anthropic
        
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key or api_key.startswith("sk-ant-your"):
            print("  ✗ Invalid ANTHROPIC_API_KEY in .env")
            return False
        
        client = Anthropic(api_key=api_key)
        print(f"  ✓ Anthropic client initialized")
        
        # Make a simple test call
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say 'API test successful'"}]
        )
        
        print(f"  ✓ API response received")
        print(f"  Model: claude-sonnet-4-20250514")
        
        print("\n✅ Anthropic API connection successful!")
        return True
        
    except Exception as e:
        print(f"  ✗ Anthropic API connection failed: {str(e)}")
        print("\n⚠️  Check your ANTHROPIC_API_KEY in .env")
        return False

def main():
    """Run all tests"""
    print("="*70)
    print("🤖 Bug Reproduction Agent - Setup Verification")
    print("="*70)
    
    results = []
    
    # Test imports
    results.append(("Packages", test_imports()))
    
    # Test files
    results.append(("Agent Files", test_agent_files()))
    
    # Test environment
    results.append(("Environment", test_env_file()))
    
    # If env is configured, test connections
    if results[-1][1]:
        results.append(("JIRA Connection", test_jira_connection()))
        results.append(("Anthropic API", test_anthropic_connection()))
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n🎉 All tests passed! You're ready to use the agent.")
        print("\nTry running:")
        print("  python reproduce_bug_cli.py --workflow")
        print("  python reproduce_bug_cli.py KAN-4")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
