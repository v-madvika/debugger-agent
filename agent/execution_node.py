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
        # Set headless to False to see the browser window
        self.headless = os.getenv("HEADLESS_BROWSER", "false").lower() == "true"
        
        print(f"ExecutionNode initialized:")
        print(f"  Use real browser: {self.use_real_browser}")
        print(f"  Headless mode: {self.headless}")
    
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
            print(f"  Headless mode: {self.headless}")
            print(f"{'='*60}")
            
            # Convert ReproductionStep objects to dict format for browser automation
            # and extract the automation data stored in actual_result
            formatted_steps = []
            for step in steps:
                step_dict = {
                    "step_number": step.step_number,
                    "action": step.action,
                    "target": step.target,
                    "description": step.description,
                    "expected_result": step.expected_result
                }
                
                # Parse automation data from actual_result field
                if step.actual_result:
                    try:
                        automation_data = json.loads(step.actual_result)
                        step_dict["selectors"] = automation_data.get("selectors", [])
                        step_dict["value"] = automation_data.get("value", "")
                        step_dict["wait_condition"] = automation_data.get("wait_condition", "")
                        step_dict["validation"] = automation_data.get("validation", "")
                        step_dict["screenshot"] = automation_data.get("screenshot", False)
                        
                        print(f"\n  Step {step.step_number}: {step.action.upper()}")
                        print(f"    Description: {step.description}")
                        if step_dict["value"]:
                            # Mask passwords
                            display_value = step_dict["value"]
                            if step.target and "password" in step.target.lower():
                                display_value = "*" * len(display_value)
                            print(f"    Value: {display_value}")
                        print(f"    Selectors: {len(step_dict['selectors'])} available")
                        
                    except (json.JSONDecodeError, TypeError) as e:
                        print(f"  ⚠ Warning: Could not parse automation data for step {step.step_number}: {e}")
                        step_dict["selectors"] = []
                        step_dict["value"] = ""
                
                formatted_steps.append(step_dict)
            
            # Use Playwright to execute steps - FORCE headless=False to see browser
            print(f"\nCalling run_browser_automation with {len(formatted_steps)} steps...")
            browser_results = run_browser_automation(formatted_steps, headless=False)  # FIX: Changed variable name
            
            print(f"Received {len(browser_results)} results from browser automation")
            
            # browser_results is already a list of ReproductionStep objects
            # No need to convert again - just return them
            executed_steps = browser_results
            
            print(f"{'='*60}")
            print(f"  Executed {len(executed_steps)} steps")
            print(f"{'='*60}\n")
            
            return executed_steps
            
        except Exception as e:
            print(f"✗ Browser automation error: {str(e)}")
            import traceback
            print(traceback.format_exc())
            
            # Mark all steps as failed and return as ReproductionStep objects
            executed_steps = []
            for step in steps:
                failed_step = ReproductionStep(
                    step_number=step.step_number,
                    description=step.description,
                    action=step.action,
                    target=step.target,
                    expected_result=step.expected_result,
                    status="failed",
                    actual_result="Failed due to automation error",
                    error=f"Browser automation error: {str(e)}"
                )
                executed_steps.append(failed_step)
            
            return executed_steps
    
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
        
        CONFIDENCE SCORE is calculated based on:
        1. Quality of data extraction (did we get numeric values?)
        2. Clarity of comparison (does observed match bug description?)
        3. Number of successful vs failed steps
        4. Completeness of verification
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
        
        # Extract verification results with better parsing
        print(f"\n   📊 Parsing Verification Results:")
        for step in executed_steps:
            if step.action == "verify" and step.status == "success":
                # Try to extract numeric value from actual_result
                value_match = re.search(r'\(Value:\s*(\d+)\)', step.actual_result)
                if value_match:
                    observed_value = value_match.group(1)
                    print(f"      Step {step.step_number}: Observed numeric value = {observed_value}")
                else:
                    # Try to find any number in the text
                    numbers = re.findall(r'\b\d+\b', step.actual_result)
                    if numbers:
                        print(f"      Step {step.step_number}: Found numbers in text: {numbers}")
                    else:
                        print(f"      Step {step.step_number}: ⚠ No numeric value found in: {step.actual_result[:100]}")
        
        prompt = f"""You are analyzing the results of a bug reproduction attempt.

**Issue**: {plan.issue_key}
**Expected Outcome**: {plan.expected_outcome}

**Executed Steps**:
{json.dumps(steps_summary, indent=2)}

**Original Bug Description**:
- Expected Behavior: {context.get('expected_behavior', 'Not specified')}
- Actual Behavior (The Bug): {context.get('actual_behavior', 'Not specified')}

**UNIVERSAL ANALYSIS RULES (Apply to ALL bugs):**

1. **Understanding "actual_result" field**:
   - Each verification step's "actual_result" contains what was observed
   - Look for patterns like "(Value: X)" which indicate extracted numeric/text values
   - Format: "Element found. Content: [text] (Value: [extracted_value])"

2. **For NUMERIC/COUNT verifications** (totals, counts, quantities):
   - Example patterns: "(Value: 3)", "(Value: 0)", "(Value: 15)"
   - The number in "(Value: X)" is the OBSERVED state
   - Compare this number with what the bug description says

3. **For TEXT/STATE verifications** (messages, labels, status):
   - Look for the actual text content in "actual_result"
   - Example: "Content: Error message displayed"
   - Compare this text with what the bug describes

4. **Determining if bug was REPRODUCED**:
   - Bug IS reproduced: Observed behavior matches the BUGGY behavior described in JIRA
   - Bug NOT reproduced: Observed behavior matches the EXPECTED/CORRECT behavior
   
   Examples:
   - JIRA says "count shows 0 when should show actual count" + observed "(Value: 0)" → Bug reproduced ✓
   - JIRA says "count shows 0" + observed "(Value: 5)" → Bug NOT reproduced ✗ (working correctly)
   - JIRA says "error message appears" + observed "Error displayed" → Bug reproduced ✓
   - JIRA says "login fails" + observed "Login successful" → Bug NOT reproduced ✗

5. **If verification incomplete** (no value extracted):
   - Example: "Found element with text: Total Tasks" (no Value: X)
   - This means the LABEL was found but NOT the actual value
   - Report as incomplete, confidence LOW (< 0.3)
   - Cannot determine bug status without actual value

6. **Confidence scoring**:
   - 0.8-1.0: Clear numeric/text value extracted, definitive match or mismatch with bug
   - 0.5-0.7: Values extracted but comparison ambiguous
   - 0.2-0.4: Only labels found, no actual values extracted
   - 0.0-0.1: Steps failed, no data to analyze

**YOUR TASK:**
Analyze the executed steps and determine:
1. Did we observe the BUGGY behavior described in JIRA? (bug_reproduced: true/false)
2. What caused the bug? (if reproduced) OR Why is system working correctly? (if not reproduced)
3. What should be done next?
4. **How confident are you in this assessment?**

**CONFIDENCE SCORE CALCULATION:**

Assign confidence based on:

**0.9-1.0** - Very High Confidence:
- Numeric value extracted clearly (e.g., "(Value: 3)")
- Definitive match or mismatch with bug description
- All critical verification steps succeeded
- No ambiguity in interpretation

**0.7-0.8** - High Confidence:
- Values extracted successfully
- Clear comparison possible
- Minor ambiguities but overall clear

**0.5-0.6** - Medium Confidence:
- Values extracted but comparison somewhat unclear
- Some steps failed but key verifications passed
- Results are mostly interpretable

**0.3-0.4** - Low Confidence:
- Only labels found, no actual values
- Example: "Found element with text: Total Tasks" (no number)
- Cannot make definitive determination

**0.1-0.2** - Very Low Confidence:
- Multiple critical steps failed
