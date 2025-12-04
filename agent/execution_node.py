"""
Execution and Verification Node
Executes bug reproduction steps using real browser automation
"""
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
from agent_state import (
    AgentState, 
    ReproductionPlan,
    ReproductionStep,
    ReproductionResult
)
from anthropic import Anthropic
from browser_automation import run_browser_automation
import os
from dotenv import load_dotenv
import boto3
import json as json_lib

load_dotenv()


class ExecutionNode:
    """
    Node for executing reproduction steps with REAL browser automation
    Uses Playwright to interact with actual applications
    """
    
    def __init__(self, use_real_browser: bool = True):
        self.use_bedrock = os.getenv("USE_BEDROCK", "false").lower() == "true"
        
        if self.use_bedrock:
            self.bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            self.model = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0")
        else:
            self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-sonnet-4-20250514"
        
        self.use_real_browser = use_real_browser
        self.headless = os.getenv("HEADLESS_BROWSER", "false").lower() == "true"
    
    def execute_steps_with_browser(
        self,
        steps: List[ReproductionStep]
    ) -> List[ReproductionStep]:
        """
        Execute reproduction steps using REAL browser automation
        
        Args:
            steps: List of steps to execute
        
        Returns:
            List of executed steps with results
        """
        try:
            print(f"\n{'='*60}")
            print("  REAL BROWSER AUTOMATION - Executing on actual application")
            print(f"{'='*60}")
            
            # Use Playwright to execute steps
            executed_steps = run_browser_automation(steps, headless=self.headless)
            
            print(f"{'='*60}")
            print(f"  Executed {len(executed_steps)} steps")
            print(f"{'='*60}\n")
            
            return executed_steps
            
        except Exception as e:
            print(f"✗ Browser automation error: {str(e)}")
            # Mark all steps as failed
            for step in steps:
                step.status = "failed"
                step.error = f"Browser automation error: {str(e)}"
                step.actual_result = "Failed due to automation error"
            return steps
    
    def simulate_step_execution(
        self,
        step: ReproductionStep,
        context: Dict[str, Any]
    ) -> ReproductionStep:
        """
        FALLBACK: Simulate execution when real browser is not available
        Only used if use_real_browser=False
        """
        
        prompt = f"""You are simulating the execution of a bug reproduction step. 

**Step Details**:
- Step Number: {step.step_number}
- Description: {step.description}
- Action: {step.action}
- Target: {step.target}
- Expected Result: {step.expected_result}

**Context**:
- Issue Key: {context.get('issue_key', 'Unknown')}
- Application: {context.get('application_name', 'Unknown')}
- Application URL: {context.get('application_url', 'Unknown')}
- Environment: {context.get('environment', 'Unknown')}
- Platform: {context.get('platform', 'Unknown')}

**Previous Steps Results**:
{json.dumps(context.get('previous_results', []), indent=2)}

Based on the bug description and step details, simulate what would happen when executing this step.

Respond in JSON format:
{{
    "status": "success|failed|skipped",
    "actual_result": "What actually happened during execution",
    "error": "Error message if failed, null otherwise"
}}

Be realistic in your simulation. If this step would likely trigger the bug based on the context, indicate that in the actual_result.
"""
        
        try:
            if self.use_bedrock:
                body = json_lib.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2048,
                    "temperature": 0.3,
                    "messages": [{"role": "user", "content": prompt}]
                })
                response = self.bedrock.invoke_model(modelId=self.model, body=body)
                response_body = json_lib.loads(response['body'].read())
                response_text = response_body['content'][0]['text']
            else:
                response = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            
            # Extract JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            result = json.loads(response_text)
            
            # Update step
            step.status = result.get("status", "success")
            step.actual_result = result.get("actual_result", "")
            step.error = result.get("error")
            
            return step
            
        except Exception as e:
            step.status = "failed"
            step.error = f"Simulation error: {str(e)}"
            step.actual_result = "Could not simulate step execution"
            return step
    
    def analyze_reproduction_results(
        self,
        plan: ReproductionPlan,
        executed_steps: List[ReproductionStep],
        context: Dict[str, Any]
    ) -> ReproductionResult:
        """
        Analyze all executed steps to determine if bug was reproduced
        and provide root cause analysis
        """
        
        steps_summary = []
        for step in executed_steps:
            steps_summary.append({
                "step": step.step_number,
                "description": step.description,
                "action": step.action,
                "expected": step.expected_result,
                "actual": step.actual_result,
                "status": step.status,
                "error": step.error
            })
        
        prompt = f"""You are analyzing the results of a bug reproduction attempt.

**Issue**: {plan.issue_key}
**Expected Outcome**: {plan.expected_outcome}

**Executed Steps**:
{json.dumps(steps_summary, indent=2)}

**Original Bug Description**:
- Expected Behavior: {context.get('expected_behavior', 'Not specified')}
- Actual Behavior: {context.get('actual_behavior', 'Not specified')}

Analyze the execution results and provide:

1. **Bug Reproduced**: Did we successfully reproduce the bug?
2. **Root Cause Analysis**: What is likely causing this bug?
3. **Recommendations**: What steps should be taken to fix it?
4. **Confidence Score**: How confident are you in this analysis? (0.0 to 1.0)

Respond in JSON format:
{{
    "bug_reproduced": true|false,
    "root_cause_analysis": "Detailed analysis of what's causing the bug",
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ],
    "confidence_score": 0.85,
    "summary": "Brief summary of findings"
}}
"""
        
        try:
            if self.use_bedrock:
                body = json_lib.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 4096,
                    "temperature": 0.3,
                    "messages": [{"role": "user", "content": prompt}]
                })
                response = self.bedrock.invoke_model(modelId=self.model, body=body)
                response_body = json_lib.loads(response['body'].read())
                response_text = response_body['content'][0]['text']
            else:
                response = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            
            # Extract JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            analysis = json.loads(response_text)
            
            # Create ReproductionResult
            result = ReproductionResult(
                issue_key=plan.issue_key,
                bug_reproduced=analysis.get("bug_reproduced", False),
                executed_steps=executed_steps,
                screenshots=[],  # Would be populated in real implementation
                logs=[f"{datetime.now().isoformat()}: Reproduction attempt completed"],
                root_cause_analysis=analysis.get("root_cause_analysis"),
                recommendations=analysis.get("recommendations", []),
                confidence_score=analysis.get("confidence_score", 0.5)
            )
            
            return result
            
        except Exception as e:
            # Create fallback result
            failed_steps = [s for s in executed_steps if s.status == "failed"]
            bug_reproduced = len(failed_steps) > 0
            
            result = ReproductionResult(
                issue_key=plan.issue_key,
                bug_reproduced=bug_reproduced,
                executed_steps=executed_steps,
                screenshots=[],
                logs=[
                    f"{datetime.now().isoformat()}: Reproduction attempt completed",
                    f"Analysis error: {str(e)}"
                ],
                root_cause_analysis=f"Could not perform detailed analysis. {len(failed_steps)} steps failed.",
                recommendations=[
                    "Manual investigation required",
                    "Review failed steps for patterns"
                ],
                confidence_score=0.3
            )
            
            return result
    
    def __call__(self, state: AgentState) -> AgentState:
        """Execute the reproduction and verification node"""
        
        messages = state.get("messages", [])
        errors = state.get("errors", [])
        
        try:
            # Get reproduction plan
            plan_dict = state.get("reproduction_plan")
            if not plan_dict:
                raise Exception("No reproduction plan found in state")
            
            plan = ReproductionPlan(**plan_dict)
            
            # Update status
            state["status"] = "executing"
            messages.append(f"\nExecuting reproduction plan ({len(plan.reproduction_steps)} steps)...")
            
            # Prepare context
            parsed_issue = state.get("parsed_issue", {})
            context = {
                "issue_key": plan.issue_key,
                "application_name": parsed_issue.get("application_details", {}).get("name"),
                "application_url": parsed_issue.get("application_details", {}).get("url"),
                "environment": parsed_issue.get("application_details", {}).get("environment"),
                "platform": parsed_issue.get("application_details", {}).get("platform"),
                "expected_behavior": parsed_issue.get("expected_behavior"),
                "actual_behavior": parsed_issue.get("actual_behavior"),
                "previous_results": []
            }
            
            # Execute steps
            messages.append(f"\n{'='*60}")
            messages.append(f"Executing {len(plan.reproduction_steps)} steps...")
            messages.append(f"Mode: {'REAL BROWSER' if self.use_real_browser else 'SIMULATION'}")
            messages.append(f"{'='*60}")
            
            if self.use_real_browser:
                # Execute with real browser automation
                executed_steps = self.execute_steps_with_browser(plan.reproduction_steps)
                
                # Log results
                for executed_step in executed_steps:
                    status_icon = "✓" if executed_step.status == "success" else "✗"
                    messages.append(f"\n  Step {executed_step.step_number}: {executed_step.description[:60]}...")
                    messages.append(f"    {status_icon} {executed_step.status.upper()}: {executed_step.actual_result[:80]}...")
                    
                    if executed_step.error:
                        messages.append(f"    Error: {executed_step.error}")
                    
                    state["current_step"] = executed_step.step_number
            else:
                # Fallback to simulation
                messages.append("⚠ Using simulation mode (set use_real_browser=True for actual execution)")
                executed_steps = []
                for i, step in enumerate(plan.reproduction_steps):
                    messages.append(f"\n  Simulating Step {step.step_number}: {step.description[:60]}...")
                    
                    executed_step = self.simulate_step_execution(step, context)
                    executed_steps.append(executed_step)
                    
                    # Update context with result
                    context["previous_results"].append({
                        "step": executed_step.step_number,
                        "status": executed_step.status,
                        "result": executed_step.actual_result
                    })
                    
                    # Log result
                    status_icon = "✓" if executed_step.status == "success" else "✗"
                    messages.append(f"    {status_icon} {executed_step.status.upper()}: {executed_step.actual_result[:80]}...")
                    
                    if executed_step.error:
                        messages.append(f"    Error: {executed_step.error}")
                    
                    state["current_step"] = i + 1
            
            # Analyze results
            messages.append("\nAnalyzing reproduction results...")
            state["status"] = "analyzing"
            
            result = self.analyze_reproduction_results(plan, executed_steps, context)
            state["reproduction_result"] = result.model_dump()
            
            # Log analysis
            messages.append(f"\n{'='*60}")
            messages.append("=== REPRODUCTION RESULT ===")
            messages.append(f"{'='*60}")
            messages.append(f"Bug Reproduced: {'YES ✓' if result.bug_reproduced else 'NO ✗'}")
            messages.append(f"Confidence: {result.confidence_score:.0%}")
            messages.append(f"\nRoot Cause Analysis:")
            messages.append(f"  {result.root_cause_analysis}")
            messages.append(f"\nRecommendations:")
            for i, rec in enumerate(result.recommendations, 1):
                messages.append(f"  {i}. {rec}")
            
            # Set status
            state["status"] = "completed"
            state["next_action"] = "report"
            
        except Exception as e:
            state["status"] = "failed"
            error_msg = f"Error in execution node: {str(e)}"
            errors.append(error_msg)
            messages.append(f"✗ {error_msg}")
            state["next_action"] = "abort"
        
        state["messages"] = messages
        state["errors"] = errors
        return state
