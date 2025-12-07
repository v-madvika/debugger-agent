"""
LangGraph Workflow Orchestrator
Main agent that coordinates all nodes in the bug reproduction workflow
"""
from typing import Dict, Any, List, Literal
from langgraph.graph import StateGraph, END
from agent_state import AgentState
from jira_parser_node import JiraParserNode
from planner_node import ReproductionPlannerNode
from execution_node import ExecutionNode
from jira_client import SimpleJiraClient
import os
import logging
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
import boto3
import json
from bedrock_client import NovaBedrockClient

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class BugReproductionAgent:
    """
    Main LangGraph agent for automated bug reproduction
    
    Workflow:
    1. Fetch and Parse JIRA Issue (JiraParserNode)
    2. Create Reproduction Plan (ReproductionPlannerNode)
    3. Execute Reproduction Steps (ExecutionNode)
    4. Generate Report
    """
    
    def __init__(self, use_real_browser: bool = True):
        """
        Initialize Bug Reproduction Agent
        
        Args:
            use_real_browser: If True, uses real browser automation (Playwright)
                            If False, uses AI simulation
        """
        logger.info("="*70)
        logger.info("Initializing BugReproductionAgent with AWS Bedrock")
        logger.info("="*70)
        
        # Log environment configuration
        model_id = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")  # Updated default
        region = os.getenv("AWS_REGION", "us-east-1")
        max_tokens = int(os.getenv("MAX_TOKENS", 2048))
        temperature = float(os.getenv("TEMPERATURE", 0.7))
        
        logger.info(f"Configuration:")
        logger.info(f"  Model/Profile ID: {model_id}")
        logger.info(f"  Region: {region}")
        logger.info(f"  Max Tokens: {max_tokens}")
        logger.info(f"  Temperature: {temperature}")
        logger.info(f"  AWS Access Key: {os.getenv('AWS_ACCESS_KEY_ID', 'NOT SET')[:10]}...")
        
        # Verify AWS credentials
        try:
            sts_client = boto3.client('sts', region_name=region)
            identity = sts_client.get_caller_identity()
            logger.info(f"✓ AWS Identity verified:")
            logger.info(f"    UserId: {identity['UserId']}")
            logger.info(f"    Account: {identity['Account']}")
            logger.info(f"    ARN: {identity['Arn']}")
        except Exception as e:
            logger.error(f"✗ AWS credentials verification failed: {str(e)}")
            raise
        
        # Check if model is accessible
        try:
            bedrock_client = boto3.client('bedrock', region_name=region)
            logger.info("Checking Bedrock model access...")
            
            # Try to get model details
            try:
                model_info = bedrock_client.get_foundation_model(modelIdentifier=model_id)
                logger.info(f"✓ Model '{model_id}' is accessible")
                logger.info(f"  Model details: {json.dumps(model_info.get('modelDetails', {}), indent=2, default=str)}")
            except Exception as e:
                logger.warning(f"Could not get model details: {str(e)}")
                logger.warning("This might mean the model needs to be enabled in Bedrock console")
        except Exception as e:
            logger.warning(f"Could not access Bedrock client: {str(e)}")
        
        # Initialize ChatBedrock with inference profile
        try:
            logger.info("Initializing ChatBedrock client with inference profile...")
            
            # Amazon Nova 2 ONLY supports these parameters
            model_kwargs = {
                "max_new_tokens": max_tokens,
                "temperature": temperature,
                "top_p": 0.9
            }
            
            logger.info(f"Model kwargs (Nova 2 compatible): {json.dumps(model_kwargs, indent=2)}")
            
            # Try using custom client first (more reliable for Nova 2)
            try:
                logger.info("Attempting to use custom NovaBedrockClient...")
                self.llm = NovaBedrockClient(
                    model_id=model_id,
                    region_name=region,
                    model_kwargs=model_kwargs
                )
                logger.info("✓ Using custom NovaBedrockClient")
            except ImportError:
                logger.info("Custom client not available, using ChatBedrock...")
                self.llm = ChatBedrock(
                    model_id=model_id,
                    region_name=region,
                    model_kwargs=model_kwargs,
                    streaming=False
                )
                logger.info("✓ Using ChatBedrock")
            
            # Test invocation
            logger.info("Testing model invocation...")
            try:
                test_response = self.llm.invoke("Reply with 'OK'")
                logger.info(f"✓ Test successful: {test_response.content[:50]}")
            except Exception as e:
                logger.error(f"✗ Test failed: {str(e)}")
                raise
            
        except Exception as e:
            logger.error(f"✗ Failed to initialize: {str(e)}")
            raise
        
        logger.info("="*70)
        
        self.jira_client = SimpleJiraClient()
        self.use_real_browser = use_real_browser
        
        # Initialize nodes
        self.jira_parser = JiraParserNode()
        self.planner = ReproductionPlannerNode()
        
        # Pass headless=False to see the browser
        self.executor = ExecutionNode(use_real_browser=use_real_browser)
        
        # Build workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        print(f"\n{'='*60}")
        print("🤖 Bug Reproduction Agent Initialized")
        print(f"{'='*60}")
        print(f"Mode: {'REAL BROWSER AUTOMATION' if use_real_browser else 'AI SIMULATION'}")
        print(f"JIRA: {os.getenv('JIRA_URL')}")
        print(f"Project: {os.getenv('JIRA_PROJECT_KEY')}")
        print(f"{'='*60}\n")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create state graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("fetch_and_parse", self.jira_parser)
        workflow.add_node("create_plan", self.planner)
        workflow.add_node("execute", self.executor)
        workflow.add_node("report", self._generate_report)
        
        # Define edges
        workflow.set_entry_point("fetch_and_parse")
        
        # Conditional routing based on state
        workflow.add_conditional_edges(
            "fetch_and_parse",
            self._route_after_parse,
            {
                "create_plan": "create_plan",
                "abort": END
            }
        )
        
        workflow.add_conditional_edges(
            "create_plan",
            self._route_after_plan,
            {
                "execute": "execute",
                "abort": END
            }
        )
        
        workflow.add_conditional_edges(
            "execute",
            self._route_after_execute,
            {
                "report": "report",
                "abort": END
            }
        )
        
        workflow.add_edge("report", END)
        
        return workflow
    
    def _route_after_parse(self, state: AgentState) -> Literal["create_plan", "abort"]:
        """Route after parsing JIRA issue"""
        next_action = state.get("next_action", "abort")
        if next_action == "plan_reproduction":
            return "create_plan"
        return "abort"
    
    def _route_after_plan(self, state: AgentState) -> Literal["execute", "abort"]:
        """Route after creating reproduction plan"""
        next_action = state.get("next_action", "abort")
        if next_action == "execute_reproduction":
            return "execute"
        return "abort"
    
    def _route_after_execute(self, state: AgentState) -> Literal["report", "abort"]:
        """Route after executing reproduction"""
        next_action = state.get("next_action", "abort")
        if next_action == "report":
            return "report"
        return "abort"
    
    def _generate_report(self, state: AgentState) -> AgentState:
        """Generate final report and optionally post to JIRA"""
        
        messages = state.get("messages", [])
        
        try:
            result = state.get("reproduction_result")
            if not result:
                raise Exception("No reproduction result found")
            
            # Generate report summary
            report_lines = [
                "\n" + "="*60,
                "=== FINAL REPRODUCTION REPORT ===",
                "="*60,
                f"Issue: {result['issue_key']}",
                f"Bug Reproduced: {'YES' if result['bug_reproduced'] else 'NO'}",
                f"Confidence Score: {result['confidence_score']:.0%}",
                f"Steps Executed: {len(result['executed_steps'])}",
                "",
                "Root Cause Analysis:",
                result['root_cause_analysis'],
                "",
                "Recommendations:",
            ]
            
            for i, rec in enumerate(result['recommendations'], 1):
                report_lines.append(f"  {i}. {rec}")
            
            report_lines.extend([
                "",
                "Detailed Steps:",
            ])
            
            for step in result['executed_steps']:
                report_lines.append(
                    f"  Step {step['step_number']}: [{step['status'].upper()}] {step['description']}"
                )
                if step.get('error'):
                    report_lines.append(f"    Error: {step['error']}")
            
            report_lines.append("="*60)
            
            messages.extend(report_lines)
            
            # Check if we should post to JIRA
            post_to_jira = os.getenv("AUTO_POST_TO_JIRA", "false").lower() == "true"
            
            if post_to_jira:
                try:
                    comment = self._format_jira_comment(result)
                    self.jira_client.add_comment(result['issue_key'], comment)
                    messages.append("\n✓ Report posted to JIRA as comment")
                except Exception as e:
                    messages.append(f"\n⚠ Failed to post to JIRA: {str(e)}")
            
            state["status"] = "completed"
            
        except Exception as e:
            messages.append(f"\n✗ Error generating report: {str(e)}")
            state["status"] = "failed"
        
        state["messages"] = messages
        return state
    
    def _format_jira_comment(self, result: Dict[str, Any]) -> str:
        """Format reproduction result as JIRA comment"""
        
        status_emoji = "✓" if result['bug_reproduced'] else "✗"
        
        comment = f"""
🤖 Automated Bug Reproduction Report

*Status*: {status_emoji} Bug {'REPRODUCED' if result['bug_reproduced'] else 'NOT REPRODUCED'}
*Confidence*: {result['confidence_score']:.0%}
*Steps Executed*: {len(result['executed_steps'])}

*Root Cause Analysis*:
{result['root_cause_analysis']}

*Recommendations*:
"""
        
        for i, rec in enumerate(result['recommendations'], 1):
            comment += f"{i}. {rec}\n"
        
        comment += f"\n_Generated by AI Bug Reproduction Agent_"
        
        return comment
    
    def reproduce_bug(
        self, 
        issue_key: str,
        code_files: Dict[str, str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point to reproduce a bug from JIRA
        
        Args:
            issue_key: JIRA issue key (e.g., 'KAN-4')
            code_files: Optional dict of filename -> code content for context
            
        Returns:
            Final state with reproduction results
        """
        
        # Initialize state
        initial_state: AgentState = {
            "jira_issue_key": issue_key,
            "raw_jira_data": None,
            "parsed_issue": None,
            "reproduction_plan": None,
            "current_step": 0,
            "reproduction_result": None,
            "messages": [],
            "errors": [],
            "status": "initializing",
            "next_action": None,
            "code_files": code_files or {},
            "github_commits": [],
            "related_issues": []
        }
        
        # Run workflow
        try:
            final_state = self.app.invoke(initial_state)
            return final_state
        except Exception as e:
            initial_state["status"] = "failed"
            initial_state["errors"].append(f"Workflow error: {str(e)}")
            return initial_state
    
    def get_workflow_diagram(self) -> str:
        """Get ASCII representation of workflow"""
        return """
Bug Reproduction Workflow:

┌─────────────────────────┐
│  Fetch & Parse JIRA     │
│  (JiraParserNode)       │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  Create Reproduction    │
│  Plan (PlannerNode)     │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  Execute Reproduction   │
│  Steps (ExecutionNode)  │
└───────────┬─────────────┘
            │
            ↓
┌─────────────────────────┐
│  Generate Report        │
└─────────────────────────┘
"""


def main():
    """
    Main entry point for bug reproduction agent
    
    Usage:
        python bug_reproduction_agent.py [ISSUE_KEY] [--simulate]
    
    Examples:
        python bug_reproduction_agent.py KAN-4
        python bug_reproduction_agent.py KAN-5 --simulate
    """
    import sys
    
    # Parse arguments
    issue_key = sys.argv[1] if len(sys.argv) > 1 else "KAN-4"
    use_real_browser = "--simulate" not in sys.argv
    
    print("\n" + "="*60)
    print("🤖 Bug Reproduction Agent - JIRA Edition")
    print("="*60)
    print(f"Issue: {issue_key}")
    print(f"Mode: {'Real Browser' if use_real_browser else 'Simulation'}")
    print("="*60 + "\n")
    
    # Initialize agent
    agent = BugReproductionAgent(use_real_browser=use_real_browser)
    
    print(agent.get_workflow_diagram())
    print(f"\nStarting bug reproduction for {issue_key}...")
    print("="*60)
    
    # Run agent
    result = agent.reproduce_bug(issue_key)
    
    # Print all messages
    print("\n".join(result.get("messages", [])))
    
    # Print errors if any
    if result.get("errors"):
        print("\n❌ ERRORS:")
        for error in result["errors"]:
            print(f"  - {error}")
    
    # Print final status
    print(f"\n{'='*60}")
    print(f"Final Status: {result.get('status', 'unknown').upper()}")
    
    if result.get("reproduction_result"):
        repro_result = result["reproduction_result"]
        print(f"Bug Reproduced: {'YES ✓' if repro_result.get('bug_reproduced') else 'NO ✗'}")
        print(f"Confidence: {repro_result.get('confidence_score', 0):.0%}")
    
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
