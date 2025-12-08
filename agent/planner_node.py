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

2. **Provide 15-20 selector strategies** including:
   - **PRIORITY 1: Find the NUMERIC VALUE container** (h1, h2, h3, span with numbers)
   - CSS ID selectors: `#element-id`
   - CSS class selectors: `.class-name`, `[class*='partial']`
   - CSS attribute selectors: `[data-testid='value']`, `[aria-label='text']`
   - XPath for headers containing numbers: `//h1[contains(text(), '0')]`, `//h2[number() >= 0]`
   - XPath for spans with numbers: `//span[contains(text(), '0')]`, `//span[number()]`
   - XPath relative to labels: `//label[contains(text(), 'Total')]/following-sibling::h2`
   - XPath relative to context: `//h5[contains(., 'TaskName')]/ancestor::div[1]//h2[number()]`
   - Generic numeric patterns: `.count`, `.metric`, `.stat-value`, `.display-number`

3. **CRITICAL for count/numeric verifications**:
   - The LABEL and the VALUE are often in SEPARATE elements
   - Example HTML: `<div><p>Total Tasks</p><h2>3</h2></div>`
   - Look for: `//p[contains(text(), 'Total')]/following-sibling::h2`
   - Look for: `//div[.//p[contains(text(), 'Total')]]//h2`
   - The NUMBER is what we need, not the label!

**NUMERIC VERIFICATION EXAMPLE:**
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
    "target": "total tasks count",
    "description": "Verify the total tasks count is displayed",
    "selectors": [
        // PRIORITY 1: Find the NUMERIC VALUE directly
        "//h2[contains(@class, 'stat')]", "//h2[contains(@class, 'count')]",
        "//h1[number() >= 0]", "//h2[number() >= 0]", "//h3[number() >= 0]",
        "//span[contains(@class, 'count')]", "//span[contains(@class, 'metric')]",
        
        // PRIORITY 2: Find value relative to label
        "//p[contains(text(), 'Total Tasks')]/following-sibling::h2",
        "//span[contains(text(), 'Total')]/following-sibling::h2",
        "//label[contains(text(), 'Total')]/following-sibling::*[self::h1 or self::h2 or self::h3]",
        
        // PRIORITY 3: Find within container
        "//div[.//p[contains(text(), 'Total Tasks')]]//h2",
        "//div[.//span[contains(text(), 'Total')]]//h2",
        
        // PRIORITY 4: Context-specific (if task name provided)
        "//h5[contains(., '{{task_name}}')]/ancestor::div[1]//h2[number()]",
        "//h5[contains(., '{{task_name}}')]/ancestor::div[1]//span[contains(@class, 'count')]",
        
        // PRIORITY 5: Generic patterns
        ".stat-value", ".metric-count", ".count", ".number", ".display-value",
        "h2", "h1", "span", "div"
    ],
    "value": "Extract and verify the numeric count",
    "wait_condition": "Numeric value is visible and loaded",
    "validation": "Extract number and compare with expected behavior",
    "screenshot": true
}}

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

**FOR COMPLEX CLICK ACTIONS (buttons within specific contexts):**

When you need to click an element that's inside a specific context (e.g., "click complete button for task 'X'"):

**CRITICAL: The context text might be in headers (h1-h6), paragraphs, spans, or divs!**

**CORRECT APPROACH - Find the header/text FIRST, then button:**
{{
    "step_number": 6,
    "action": "click",
    "target": "{{describe the button and context from JIRA}}",
    "description": "{{description from JIRA step}}",
    "selectors": [
        // STRATEGY 1: Find header with context text, then button in same container
        "//h1[contains(., '{{exact_context_text}}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]",
        "//h2[contains(., '{{exact_context_text}}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]",
        "//h3[contains(., '{{exact_context_text}}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]",
        "//h4[contains(., '{{exact_context_text}}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]",
        "//h5[contains(., '{{exact_context_text}}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]",
        "//h6[contains(., '{{exact_context_text}}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]",
        
        // STRATEGY 2: Find header, go up to parent card/container, find any button
        "//h5[contains(., '{{exact_context_text}}')]/ancestor::div[contains(@class, 'card')]//button",
        "//h5[contains(., '{{exact_context_text}}')]/ancestor::div[contains(@class, 'row')]//button",
        "//h5[contains(., '{{exact_context_text}}')]/ancestor::*[self::div or self::li or self::tr][1]//button",
        
        // STRATEGY 3: Traditional container-based search
        "//div[contains(., '{{exact_context_text}}')]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]",
        "//li[contains(., '{{exact_context_text}}')]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]",
        "//tr[contains(., '{{exact_context_text}}')]//button",
        
        // STRATEGY 4: Case-insensitive header search
        "//h5[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{context_lowercase}}')]/ancestor::div[1]//button",
        
        // STRATEGY 5: CSS with Playwright (if headers support :has-text)
        ".card:has-text('{{exact_context_text}}') button:has-text('{{button_text}}')",
        ".task-item:has-text('{{exact_context_text}}') button:has-text('{{button_text}}')",
        
        // STRATEGY 6: Data attributes
        "[data-task-name='{{exact_context_text}}'] button",
        "[data-item-name='{{exact_context_text}}'] button",
        
        // STRATEGY 7: Generic button search (LAST RESORT)
        "button:has-text('{{button_text}}')",
        "button[type='button']", "button"
    ],
    "wait_condition": "Button is visible and enabled"
}}

**EXAMPLE - HTML Structure:**
```html
<div class="card">
    <h5>{{Task Name Here}}</h5>
    <button class="complete-btn">{{Button Text}}</button>
</div>
```

**CORRECT selectors (in priority order):**
Replace `{{exact_context_text}}` with the ACTUAL task name from JIRA, and `{{button_text}}` with the ACTUAL button text:

1. `"//h5[contains(., '{{exact_context_text}}')]/ancestor::div[1]//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{{button_text_lowercase}}')]"` ← BEST
2. `"//h5[contains(., '{{exact_context_text}}')]/ancestor::div[contains(@class, 'card')]//button"` ← Find card container
3. `".card:has-text('{{exact_context_text}}') button:has-text('{{button_text}}')"` ← CSS approach
4. `"//div[contains(., '{{exact_context_text}}')]//button[contains(., '{{button_text}}')]"` ← Traditional
5. `"button:has-text('{{button_text}}')"` ← LAST RESORT (will click first matching button!)

**KEY XPATH CONCEPTS:**
- `//h5[contains(., 'text')]` = Find h5 tag containing this text (any text from JIRA)
- `/ancestor::div[1]` = Navigate UP to the first parent div element
- `/ancestor::div[contains(@class, 'card')]` = Navigate UP to div with class 'card'
- `//button` = Then find any button descendant within that container
- `[contains(translate(text(), 'ABC...', 'abc...'), 'lowercase')]` = Case-insensitive button text match

**IMPORTANT RULES:**
1. **Check ALL header levels**: h1, h2, h3, h4, h5, h6 - use the appropriate one based on page structure
2. **Use ancestor:: to go UP**: Navigate from the identifying element (header/text) to its parent container
3. **Look for common classes**: 'card', 'task', 'item', 'row', 'list-item', 'col', 'container'
4. **Case-insensitive matching**: Always use translate() in XPath for robustness across different text cases
5. **Extract exact text from JIRA**: Use the PRECISE text from the JIRA description (preserve quotes, spacing, capitalization)
6. **Replace placeholders**: 
   - `{{exact_context_text}}` → actual identifier text from JIRA (e.g., task name, item title, card header)
   - `{{context_lowercase}}` → lowercase version for case-insensitive matching
   - `{{button_text}}` → actual button text from JIRA (e.g., "Complete", "Delete", "Edit")
   - `{{button_text_lowercase}}` → lowercase version (e.g., "complete", "delete", "edit")

**COMMON PATTERNS TO RECOGNIZE:**
- "click complete button for task 'ABC'" → context='ABC', button='complete'
- "delete item named 'XYZ'" → context='XYZ', button='delete'
- "edit the 'My Project' entry" → context='My Project', button='edit'

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
3. **For click actions with context**: Provide 12-15 DIVERSE selectors (CSS, XPath, text, attributes, generic)
4. **For verification steps**: Add WAIT step before verification, then provide 10-15 selector variations
5. **For navigation steps**: Add appropriate wait times for page loads
6. Use the ACTUAL credentials, URLs, and field names from the JIRA ticket
7. Add screenshots at critical points (after login, before/after key actions, at verification points)

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
