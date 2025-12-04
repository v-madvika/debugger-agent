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
        
        prompt = f"""You are an expert QA automation engineer creating an EXECUTABLE bug reproduction plan.

**CRITICAL**: This plan will be executed by an automated browser agent. Each step MUST be precise and actionable.

## JIRA Issue: {issue_details.issue_key}
**Summary**: {issue_details.summary}
**Type**: {issue_details.issue_type}
**Priority**: {issue_details.priority}

### Bug Description:
{issue_details.description}

### Original Reproduction Steps from JIRA:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(issue_details.reproduction_steps))}

### Expected vs Actual Behavior:
- **Expected**: {issue_details.expected_behavior or "Not specified"}
- **Actual (BUG)**: {issue_details.actual_behavior or "Not specified"}

### Application Information:
- **URL**: {app_url} (WILL BE ACCESSED AUTOMATICALLY)
- **Name**: {issue_details.application_details.name}
- **Environment**: {issue_details.application_details.environment}
- **Platform**: {issue_details.application_details.platform}
{f"- **Login**: username={credentials.get('username', 'N/A')}, password={'***' if credentials.get('password') else 'N/A'}" if credentials else ""}

{code_context}

---

Create an AUTOMATED reproduction plan with SPECIFIC, EXECUTABLE instructions:

{{
    "prerequisites": [
        "Chrome/Firefox browser installed",
        "Internet connection",
        "Any other requirements"
    ],
    "environment_setup": {{
        "required_tools": ["selenium", "playwright"],
        "browser": "chrome",
        "window_size": "1920x1080",
        "timeout": 30
    }},
    "reproduction_steps": [
        {{
            "step_number": 1,
            "description": "Navigate to application homepage",
            "action": "navigate",
            "target": "{app_url}",
            "expected_result": "Page loads successfully"
        }},
        {{
            "step_number": 2,
            "description": "Click on specific button/link",
            "action": "click",
            "target": "css:#button-id" or "xpath://button[@id='submit']" or "text:Button Text",
            "expected_result": "Button is clicked and action triggered"
        }},
        {{
            "step_number": 3,
            "description": "Enter text in input field",
            "action": "input",
            "target": "css:#input-id or name:fieldName",
            "expected_result": "Text is entered in field",
            "data": "text to enter"
        }},
        {{
            "step_number": 4,
            "description": "Verify expected element appears",
            "action": "verify",
            "target": "css:.success-message",
            "expected_result": "Success message is visible"
        }}
    ],
    "expected_outcome": "Detailed description of what should happen when bug is reproduced"
}}

**CRITICAL REQUIREMENTS**:

1. **Action Types** (use these EXACT values):
   - "navigate": Go to URL (target must be full URL)
   - "click": Click element (target must be valid selector)
   - "input": Type text (target = field selector, include "data" field)
   - "select": Select dropdown option (target = selector, include "data" field with option)
   - "wait": Wait for element (target = selector to wait for)
   - "verify": Check if element exists/visible (target = selector to verify)
   - "screenshot": Take screenshot at this point
   - "execute_js": Run JavaScript (include "data" field with JS code)

2. **Selector Formats** (target field):
   - CSS: "css:#element-id" or "css:.class-name"
   - XPath: "xpath://button[@id='submit']"
   - Text: "text:Click Here"
   - Name: "name:fieldName"
   - ID: "id:element-id"

3. **Step Structure**:
   - Start with "navigate" to {app_url}
   - Include login steps if credentials exist
   - Follow JIRA reproduction steps exactly
   - Add "verify" steps to check if bug occurred
   - End with verification of the bug symptom

4. **Be Specific**:
   - Use actual element IDs, classes from the application
   - Include specific data values to enter
   - Add wait steps before verifying elements
   - Include screenshot steps at critical points

Respond ONLY with valid JSON, no additional text or markdown.
"""
        
        try:
            if self.use_bedrock:
                body = json_lib.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 8192,
                    "temperature": 0.3,
                    "messages": [{"role": "user", "content": prompt}]
                })
                response = self.bedrock.invoke_model(modelId=self.model, body=body)
                response_body = json_lib.loads(response['body'].read())
                response_text = response_body['content'][0]['text']
            else:
                response = self.anthropic.messages.create(
                    model=self.model,
                    max_tokens=8192,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = response.content[0].text
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
            
            parsed_plan = json.loads(response_text)
            
            # Convert to ReproductionStep objects with validation
            repro_steps = []
            for step_data in parsed_plan.get("reproduction_steps", []):
                # Validate required fields
                if not step_data.get("action"):
                    raise Exception(f"Step {step_data.get('step_number')} missing action")
                
                step = ReproductionStep(
                    step_number=step_data.get("step_number", len(repro_steps) + 1),
                    description=step_data.get("description", ""),
                    action=step_data.get("action", "execute"),
                    target=step_data.get("target"),
                    expected_result=step_data.get("expected_result"),
                    status="pending"
                )
                
                # Store additional data in actual_result field temporarily
                if step_data.get("data"):
                    step.actual_result = f"DATA:{step_data['data']}"
                
                repro_steps.append(step)
            
            if not repro_steps:
                raise Exception("No reproduction steps were generated")
            
            # Create ReproductionPlan
            plan = ReproductionPlan(
                issue_key=issue_details.issue_key,
                reproduction_steps=repro_steps,
                prerequisites=parsed_plan.get("prerequisites", []),
                environment_setup=parsed_plan.get("environment_setup", {}),
                expected_outcome=parsed_plan.get("expected_outcome", "Bug should be reproduced")
            )
            
            return plan
            
        except json.JSONDecodeError as e:
            raise Exception(f"Failed to parse Claude response as JSON: {str(e)}\nResponse: {response_text}")
        except Exception as e:
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
