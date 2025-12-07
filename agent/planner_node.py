"""
Bug Reproduction Planner Node
Creates detailed execution plan for reproducing bugs
"""
import json
import re
from typing import Dict, Any, List
from agent_state import (
    AgentState, 
    JiraIssueDetails, 
    ReproductionPlan, 
    ReproductionStep,
    ApplicationDetails
)
from anthropic import Anthropic
import os
from dotenv import load_dotenv
import boto3
import json as json_lib

load_dotenv()


class ReproductionPlannerNode:
    """Node for creating detailed bug reproduction plan"""
    
    def __init__(self):
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
    
    def create_reproduction_plan(
        self, 
        issue_details: JiraIssueDetails,
        code_files: Dict[str, str] = None
    ) -> ReproductionPlan:
        """
        Use Claude to create a detailed, executable reproduction plan
        """
        
        code_context = ""
        if code_files:
            code_context = "\n\n### Available Code Files:\n"
            for filename, content in code_files.items():
                code_context += f"\n**{filename}**:\n```\n{content[:1000]}...\n```\n"
        
        # Get application URL - CRITICAL for automation
        app_url = issue_details.application_details.url
        if not app_url:
            raise Exception("Application URL is required but not found in JIRA ticket")
        
        credentials = issue_details.application_details.additional_info.get("credentials", {})
        
        prompt = f"""You are an expert at creating detailed, executable browser automation plans for bug reproduction.

**CRITICAL INSTRUCTIONS:**

You will receive bug reproduction steps from a JIRA ticket. Convert these into precise, executable automation steps.

**FOR LOGIN STEPS:**
When a step mentions "login", "sign in", or "enter credentials", break it into detailed substeps:
1. Fill email/username field (use actual credentials provided)
2. Fill password field (use actual credentials provided)
3. Click the login/submit button
4. **ADD a wait step (3-5 seconds) to allow page navigation and data loading**

**EXAMPLE LOGIN SEQUENCE:**
{{
    "step_number": 2,
    "action": "fill",
    "target": "Email Address field",
    "value": "actual_email_from_credentials",
    "description": "Enter email in login form",
    "selectors": ["#email", "input[name='email']", "input[type='email']", ...],
    "wait_condition": "input is visible and enabled"
}},
{{
    "step_number": 3,
    "action": "fill",
    "target": "password field",
    "value": "actual_password_from_credentials",
    "description": "Enter password in login form",
    "selectors": ["#password", "input[type='password']", ...],
    "wait_condition": "input is visible and enabled"
}},
{{
    "step_number": 4,
    "action": "click",
    "target": "login button",
    "description": "Click login button",
    "selectors": ["#login-btn", "button[type='submit']", ...],
    "wait_condition": "button is enabled"
}},
{{
    "step_number": 5,
    "action": "wait",
    "target": "page load",
    "value": "3000",
    "description": "Wait for page to load after login",
    "wait_condition": "Navigation complete and page fully loaded"
}}

**FOR VERIFICATION STEPS:**
When creating steps that verify content, state, or data (ANY kind of verification):

1. **Always add a wait step BEFORE verification** to ensure:
   - AJAX/API calls have completed
   - Dynamic content has loaded
   - Animations have finished

2. **Provide 10-15 selector strategies** including:
   - CSS ID selectors: `#element-id`
   - CSS class selectors: `.class-name`, `[class*='partial']`
   - CSS attribute selectors: `[data-testid='value']`, `[aria-label='text']`
   - XPath text search: `//span[contains(text(), 'keyword')]`
   - XPath case-insensitive: `//div[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'keyword')]`
   - Playwright text selectors: `text=/pattern/i`
   - Relative XPath: `//h3[contains(text(), 'Label')]/following-sibling::span`
   - Generic class patterns: `.stat`, `.metric`, `.count`, `.value`

3. **Be specific about what to verify:**
   - Text content match
   - Numeric value comparison
   - Element visibility
   - Element state (enabled/disabled)
   - Count of elements

**GENERIC VERIFICATION EXAMPLE:**
{{
    "step_number": 7,
    "action": "wait",
    "target": "data loading",
    "value": "2000",
    "description": "Wait for dynamic content to load",
    "wait_condition": "Page fully loaded with all data"
}},
{{
    "step_number": 8,
    "action": "verify",
    "target": "{{describe what to verify based on JIRA step}}",
    "description": "{{verification description from JIRA}}",
    "selectors": [
        "//span[contains(text(), '{{keyword from JIRA}}')]",
        "//div[contains(@class, '{{relevant-class}}')]",
        "#{{likely-id}}",
        ".{{likely-class}}",
        "[data-testid='{{relevant-testid}}']",
        "text=/{{pattern from JIRA}}/i",
        "//label[contains(text(), '{{label}}')]/following-sibling::*",
        ".stat-value", ".metric", ".count", ".display-value",
        "span", "div", "h1", "h2", "h3", "p"
    ],
    "value": "{{what value to check or extract}}",
    "wait_condition": "Element is visible and contains expected data",
    "validation": "{{how to validate - e.g., 'check if not zero', 'verify text matches', 'count should be > 0'}}",
    "screenshot": true
}}

**TASK:**

Create a detailed reproduction plan for this bug:

Issue: {issue_details.issue_key}
Summary: {issue_details.summary}

Application Details:
- URL: {issue_details.application_details.url}
- Platform: {issue_details.application_details.platform}
- Credentials: {json.dumps(credentials, indent=2) if credentials else "No credentials provided"}

**Reproduction Steps from JIRA Ticket:**
{json.dumps(issue_details.reproduction_steps, indent=2)}

**Expected Behavior:**
{issue_details.expected_behavior}

**Actual Behavior (The Bug):**
{issue_details.actual_behavior}

{code_context}

**YOUR TASK:**

1. Convert each JIRA reproduction step into detailed automation steps
2. **For login steps**: Break into fill email → fill password → click button → WAIT for page load
3. **For verification steps**: Add WAIT step before verification, then provide 10-15 selector variations
4. **For navigation steps**: Add appropriate wait times for page loads
5. Use the ACTUAL credentials, URLs, and field names from the JIRA ticket
6. Add screenshots at critical points (after login, before/after key actions, at verification points)

Return ONLY valid JSON (no markdown, no explanations):
{{
    "plan_id": "{issue_details.issue_key}-plan",
    "issue_key": "{issue_details.issue_key}",
    "estimated_duration_seconds": 180,
    "prerequisites": ["Browser must be installed", "Network access to {issue_details.application_details.url}"],
    "environment_setup": {{
        "application_url": "{issue_details.application_details.url}",
        "credentials": {json.dumps(credentials)}
    }},
    "reproduction_steps": [
        {{
            "step_number": 1,
            "action": "navigate",
            "target": "application URL",
            "value": "{issue_details.application_details.url}",
            "description": "Navigate to the application",
            "selectors": [],
            "wait_condition": "page is loaded",
            "expected_result": "Application homepage is displayed",
            "screenshot": true
        }}
        // ... more steps based on JIRA reproduction steps
        // CRITICAL: Break down login into: fill email, fill password, click, WAIT
        // CRITICAL: Before ANY verification: add WAIT step, then provide 10-15 selectors
    ],
    "expected_outcome": "{issue_details.expected_behavior}",
    "success_criteria": [
        "All reproduction steps completed successfully",
        "Bug behavior observed: {issue_details.actual_behavior[:100]}..."
    ]
}}

**REMEMBER:**
- Break login into 4 steps: fill email, fill password, click, WAIT
- Add WAIT step before every verification
- Provide 10-15 diverse selectors for verifications (CSS, XPath, text-based)
- Use actual credentials from the environment_setup section
- Be specific about what to verify based on the JIRA ticket description
- DO NOT hardcode specific bug details - make it generic and adaptable
"""
        
        try:
            if self.use_bedrock:
                # AWS Bedrock Converse API (for Nova 2)
                print("\n📋 Creating reproduction plan with Nova 2...")
                print(f"   Application URL: {app_url}")
                print(f"   Credentials available: {bool(credentials)}")
                print(f"   JIRA steps count: {len(issue_details.reproduction_steps)}")
                
                response = self.bedrock.converse(
                    modelId=self.model,
                    messages=[{
                        "role": "user",
                        "content": [{"text": prompt}]
                    }],
                    inferenceConfig={
                        "maxTokens": 4096,
                        "temperature": 0.0,
                        "topP": 0.9
                    }
                )
                response_text = response['output']['message']['content'][0]['text']
                print(f"   ✓ Received plan from Nova 2 ({len(response_text)} chars)")
            else:
                # Anthropic API
                response = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=4096,
                    temperature=0,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                response_text = response.content[0].text
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            parsed_plan = json.loads(response_text)
            
            print(f"   ✓ Plan parsed successfully")
            print(f"   Generated steps: {len(parsed_plan.get('reproduction_steps', []))}")
            
            # Convert to ReproductionStep objects
            repro_steps = []
            for step_data in parsed_plan.get("reproduction_steps", []):
                # Validate required fields
                if not step_data.get("action"):
                    raise Exception(f"Step {step_data.get('step_number')} missing action")
                
                # Create step with all fields
                step = ReproductionStep(
                    step_number=step_data.get("step_number", len(repro_steps) + 1),
                    description=step_data.get("description", ""),
                    action=step_data.get("action", "execute"),
                    target=step_data.get("target"),
                    expected_result=step_data.get("expected_result"),
                    status="pending"
                )
                
                # Store additional automation data (selectors, value, etc.)
                step.actual_result = json.dumps({
                    "selectors": step_data.get("selectors", []),
                    "value": step_data.get("value", ""),
                    "wait_condition": step_data.get("wait_condition", ""),
                    "validation": step_data.get("validation", ""),
                    "screenshot": step_data.get("screenshot", False)
                })
                
                repro_steps.append(step)
                
                # Log important steps
                if step.action == "fill":
                    print(f"   Step {step.step_number}: Fill '{step.target}' with '{step_data.get('value', '')[:20]}...'")
                elif step.action == "click":
                    print(f"   Step {step.step_number}: Click '{step.target}'")
            
            if not repro_steps:
                raise Exception("No reproduction steps were generated")
            
            # Create ReproductionPlan
            plan = ReproductionPlan(
                issue_key=issue_details.issue_key,
                reproduction_steps=repro_steps,
                prerequisites=parsed_plan.get("prerequisites", []),
                environment_setup=parsed_plan.get("environment_setup", {}),
                expected_outcome=parsed_plan.get("expected_outcome", issue_details.expected_behavior)
            )
            
            return plan
            
        except json.JSONDecodeError as e:
            print(f"   ✗ JSON parsing failed")
            print(f"   Response: {response_text[:500]}")
            raise Exception(f"Failed to parse Claude response as JSON: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            print(f"   ✗ Plan creation failed: {str(e)}")
            raise Exception(f"Failed to create reproduction plan: {str(e)}")
    
    def validate_plan(self, plan: ReproductionPlan) -> List[str]:
        """Validate the reproduction plan for completeness"""
        issues = []
        
        if not plan.reproduction_steps:
            issues.append("No reproduction steps defined")
        
        if len(plan.reproduction_steps) < 2:
            issues.append("Reproduction plan should have at least 2 steps")
        
        # Check if there's at least one verification step
        has_verify = any(step.action == "verify" for step in plan.reproduction_steps)
        if not has_verify:
            issues.append("Plan should include verification steps")
        
        # Check for missing expected results
        missing_expected = [
            step.step_number 
            for step in plan.reproduction_steps 
            if not step.expected_result and step.action == "verify"
        ]
        if missing_expected:
            issues.append(f"Steps {missing_expected} are missing expected results")
        
        return issues
    
    def __call__(self, state: AgentState) -> AgentState:
        """Execute the reproduction planner node"""
        
        messages = state.get("messages", [])
        errors = state.get("errors", [])
        
        try:
            # Get parsed issue
            parsed_issue_dict = state.get("parsed_issue")
            if not parsed_issue_dict:
                raise Exception("No parsed issue found in state")
            
            # Convert dict back to JiraIssueDetails
            parsed_issue = JiraIssueDetails(**parsed_issue_dict)
            
            # Update status
            state["status"] = "planning"
            messages.append("Creating detailed reproduction plan with Claude...")
            
            # Get code files if available
            code_files = state.get("code_files", {})
            
            # Create plan
            plan = self.create_reproduction_plan(parsed_issue, code_files)
            
            # Validate plan
            validation_issues = self.validate_plan(plan)
            if validation_issues:
                messages.append("⚠ Plan validation warnings:")
                for issue in validation_issues:
                    messages.append(f"  - {issue}")
            
            # Store plan in state
            state["reproduction_plan"] = plan.model_dump()
            state["current_step"] = 0
            
            messages.append(f"✓ Created reproduction plan with {len(plan.reproduction_steps)} steps")
            messages.append(f"  Prerequisites: {len(plan.prerequisites)}")
            messages.append(f"  Expected outcome: {plan.expected_outcome[:100]}...")
            
            # Show plan summary
            messages.append("\n=== Reproduction Plan ===")
            for step in plan.reproduction_steps:
                messages.append(
                    f"  Step {step.step_number}: [{step.action.upper()}] {step.description[:80]}..."
                )
            
            # Set next action
            state["status"] = "planned"
            state["next_action"] = "execute_reproduction"
            
        except Exception as e:
            state["status"] = "failed"
            error_msg = f"Error in reproduction planner: {str(e)}"
            errors.append(error_msg)
            messages.append(f"✗ {error_msg}")
            state["next_action"] = "abort"
        
        state["messages"] = messages
        state["errors"] = errors
        return state
