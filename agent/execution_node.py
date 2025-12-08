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
4. How confident are you in this assessment?

Respond in JSON format:
{{
    "bug_reproduced": true|false,
    "root_cause_analysis": "Detailed analysis based on observed vs expected behavior",
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "confidence_score": 0.85,
    "summary": "Concise summary of findings"
}}
"""
        
        try:
            if self.use_bedrock:
                # Use Converse API for Nova 2
                response = self.bedrock.converse(
                    modelId=self.model,
                    messages=[{
                        "role": "user",
                        "content": [{"text": prompt}]
                    }],
                    inferenceConfig={
                        "maxTokens": 4096,
                        "temperature": 0.3,
                        "topP": 0.9
                    }
                )
                response_text = response['output']['message']['content'][0]['text']
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
                screenshots=[],
                logs=[f"{datetime.now().isoformat()}: Reproduction attempt completed"],
                root_cause_analysis=analysis.get("root_cause_analysis"),
                recommendations=analysis.get("recommendations", []),
                confidence_score=analysis.get("confidence_score", 0.5)
            )
            
            return result
            
        except Exception as e:
            print(f"   ⚠ Analysis failed: {str(e)}")
            
            # Generic fallback logic (works for any bug type)
            failed_steps = [s for s in executed_steps if s.status == "failed"]
            success_steps = [s for s in executed_steps if s.status == "success"]
            verify_steps = [s for s in executed_steps if s.action == "verify" and s.status == "success"]
            
            bug_reproduced = False
            root_cause = "Automated analysis failed. "
            confidence = 0.3
            
            if verify_steps:
                # Try to extract any values from verification steps
                values_found = []
                for v_step in verify_steps:
                    # Look for "(Value: X)" pattern
                    value_match = re.search(r'\(Value:\s*([^\)]+)\)', v_step.actual_result)
                    if value_match:
                        values_found.append({
                            "step": v_step.step_number,
                            "value": value_match.group(1),
                            "description": v_step.description
                        })
                
                if values_found:
                    root_cause += f"Found {len(values_found)} verification value(s): {values_found}. "
                    confidence = 0.5
                    # Cannot automatically determine bug status without knowing expected values
                    root_cause += "Manual comparison with bug description required."
                else:
                    root_cause += "Verifications succeeded but no values extracted. "
                    confidence = 0.2
            
            if len(failed_steps) > len(success_steps):
                root_cause += f"{len(failed_steps)} steps failed. "
                confidence = 0.1
            
            result = ReproductionResult(
                issue_key=plan.issue_key,
                bug_reproduced=bug_reproduced,
                executed_steps=executed_steps,
                screenshots=[],
                logs=[
                    f"{datetime.now().isoformat()}: Reproduction attempt completed",
                    f"Analysis error: {str(e)}",
                    f"Successful steps: {len(success_steps)}/{len(executed_steps)}",
                    f"Failed steps: {len(failed_steps)}/{len(executed_steps)}"
                ],
                root_cause_analysis=root_cause,
                recommendations=[
                    "Review execution screenshots for actual observed behavior",
                    "Manually compare observed values with bug description",
                    "Check verification step results for extracted values",
                    "Improve selectors if values were not extracted"
                ],
                confidence_score=confidence
            )
            
            return result
    
    def analyze_execution_with_claude(self, execution_results: List[Dict]) -> Dict:
        """Analyze execution results with Claude"""
        
        # Prepare prompt for analysis
        prompt = f"""You are analyzing the results of a bug reproduction attempt.

**Executed Steps Results**:
{json.dumps(execution_results, indent=2)}

Provide a summary of the execution, including:

- Were there any errors? (yes/no)
- If errors occurred, list the steps that failed and the error messages.
- Based on the execution, do you think the bug was reproduced? (yes/no)
- Any other relevant observations.

Respond in JSON format:
{{
    "errors_occurred": true|false,
    "failed_steps": [
        {{
            "step": 1,
            "error": "Error message here"
        }}
    ],
    "bug_reproduced": true|false,
    "observations": "Any other relevant observations"
}}
"""
        
        try:
            if self.use_bedrock:
                # AWS Bedrock Converse API (for Nova 2)
                response = self.bedrock.converse(
                    modelId=self.model,
                    messages=[{
                        "role": "user",
                        "content": [{"text": prompt}]
                    }],
                    inferenceConfig={
                        "maxTokens": 2048,
                        "temperature": 0.0,
                        "topP": 0.9
                    }
                )
                response_text = response['output']['message']['content'][0]['text']
            else:
                # Anthropic API
                response = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    temperature=0,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                response_text = response.content[0].text
            
            # Extract JSON
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            analysis = json.loads(response_text)
            
            return analysis
        
        except Exception as e:
            return {
                "errors_occurred": True,
                "failed_steps": [],
                "bug_reproduced": False,
                "observations": f"Error during analysis: {str(e)}"
            }
    
    async def _execute_fill_action(self, page, step: Dict) -> Dict[str, Any]:
        """Execute fill action with multiple selector attempts"""
        
        print(f"    Executing FILL action: {step['description']}")
        
        target = step.get('target', '')
        value = step.get('value', '')
        selectors = step.get('selectors', [])
        
        if not selectors:
            # Generate fallback selectors based on target description
            selectors = self._generate_fallback_selectors(target)
        
        print(f"    Target: {target}")
        print(f"    Value: {value[:20]}..." if len(value) > 20 else f"    Value: {value}")
        print(f"    Trying {len(selectors)} selector(s)...")
        
        last_error = None
        
        for i, selector in enumerate(selectors, 1):
            try:
                print(f"      [{i}/{len(selectors)}] Trying selector: {selector}")
                
                # Wait for element with timeout
                await page.wait_for_selector(selector, timeout=5000, state='visible')
                
                # Clear existing value first
                await page.fill(selector, '')
                await page.wait_for_timeout(200)
                
                # Fill with new value
                await page.fill(selector, value)
                await page.wait_for_timeout(300)
                
                # Verify the value was entered
                entered_value = await page.input_value(selector)
                
                if entered_value == value:
                    print(f"      ✓ Successfully filled field with selector: {selector}")
                    return {
                        "status": "success",
                        "selector_used": selector,
                        "message": f"Filled '{target}' with value"
                    }
                else:
                    print(f"      ⚠ Value mismatch. Expected: {value}, Got: {entered_value}")
                    last_error = f"Value verification failed for {selector}"
                    
            except Exception as e:
                print(f"      ✗ Selector failed: {str(e)[:100]}")
                last_error = str(e)
                continue
        
        # All selectors failed
        error_msg = f"Failed to fill '{target}' after trying {len(selectors)} selectors. Last error: {last_error}"
        print(f"    ✗ {error_msg}")
        
        # Take screenshot for debugging
        screenshot_path = f"failed_fill_{step.get('step_number', 'unknown')}.png"
        await page.screenshot(path=screenshot_path)
        print(f"    📸 Debug screenshot saved: {screenshot_path}")
        
        return {
            "status": "failed",
            "error": error_msg,
            "selectors_tried": selectors,
            "screenshot": screenshot_path
        }
    
    def _generate_fallback_selectors(self, target_description: str) -> List[str]:
        """Generate fallback selectors based on target description"""
        
        selectors = []
        target_lower = target_description.lower()  # FIX: Added missing ()
        
        # Email field patterns
        if 'email' in target_lower or 'username' in target_lower or 'user' in target_lower:
            selectors.extend([
                "#email", "#username", "#user", "#login-email", "#user-email",
                "input[name='email']", "input[name='username']", "input[name='user']",
                "input[type='email']", "input[type='text']",
                "input[placeholder*='email' i]", "input[placeholder*='username' i]",
                ".email-input", ".login-email", ".user-email",
                "input[aria-label*='email' i]", "input[aria-label*='username' i]",
                "input[data-testid='email']", "input[data-testid='username']",
                "input[autocomplete='email']", "input[autocomplete='username']"
            ])
        
        # Password field patterns
        elif 'password' in target_lower or 'pass' in target_lower:
            selectors.extend([
                "#password", "#passwd", "#pass", "#user-password", "#login-password",
                "input[name='password']", "input[name='passwd']", "input[name='pass']",
                "input[type='password']",
                "input[placeholder*='password' i]",
                ".password-input", ".login-password",
                "input[aria-label*='password' i]",
                "input[data-testid='password']",
                "input[autocomplete='current-password']"
            ])
        
        # Button patterns
        elif 'button' in target_lower or 'submit' in target_lower or 'login' in target_lower or 'sign in' in target_lower:
            selectors.extend([
                "button[type='submit']",
                "button:has-text('Log in')", "button:has-text('Login')", "button:has-text('Sign in')",
                "button:has-text('LOG IN')", "button:has-text('SIGN IN')",
                "input[type='submit']",
                "#login-button", "#submit", "#signin",
                ".login-button", ".btn-login", ".submit-button",
                "button[name='login']", "button[name='submit']",
                "a:has-text('Log in')", "a:has-text('Sign in')"
            ])
        
        # Generic input patterns
        else:
            selectors.extend([
                "input[type='text']",
                "input:visible",
                ".form-control",
                "[data-testid]",
                "input"
            ])
        
        return selectors
    
    async def _execute_click_action(self, page, step: Dict) -> Dict[str, Any]:
        """Execute click action with multiple selector attempts"""
        
        print(f"    Executing CLICK action: {step['description']}")
        
        target = step.get('target', '')
        selectors = step.get('selectors', [])
        
        if not selectors:
            selectors = self._generate_fallback_selectors(target)
        
        print(f"    Target: {target}")
        print(f"    Trying {len(selectors)} selector(s)...")
        
        last_error = None
        
        for i, selector in enumerate(selectors, 1):
            try:
                print(f"      [{i}/{len(selectors)}] Trying selector: {selector}")
                
                # Wait for element
                await page.wait_for_selector(selector, timeout=5000, state='visible')
                
                # Click the element
                await page.click(selector)
                await page.wait_for_timeout(500)
                
                print(f"      ✓ Successfully clicked: {selector}")
                return {
                    "status": "success",
                    "selector_used": selector,
                    "message": f"Clicked '{target}'"
                }
                
            except Exception as e:
                print(f"      ✗ Selector failed: {str(e)[:100]}")
                last_error = str(e)
                continue
        
        error_msg = f"Failed to click '{target}' after trying {len(selectors)} selectors"
        print(f"    ✗ {error_msg}")
        
        return {
            "status": "failed",
            "error": error_msg,
            "selectors_tried": selectors
        }
    
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
