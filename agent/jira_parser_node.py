"""
JIRA Issue Fetcher and Parser Node
"""
import json
import re
from typing import Dict, Any, Optional, List
from agent_state import AgentState, JiraIssueDetails, ApplicationDetails, NodeOutput
from jira_client import SimpleJiraClient
from anthropic import Anthropic
import os
from dotenv import load_dotenv
import boto3
import json as json_lib

load_dotenv()


class JiraParserNode:
    """Node for fetching and parsing JIRA issues"""
    
    def __init__(self):
        self.jira_client = SimpleJiraClient()
        self.use_bedrock = os.getenv("USE_BEDROCK", "false").lower() == "true"
        
        if self.use_bedrock:
            # AWS Bedrock setup - Use Converse API for Nova 2
            self.bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv("AWS_REGION", "us-east-1"),
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            # Use inference profile ID for Nova 2
            self.model = os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-lite-v1:0")
            print(f"✓ Using AWS Bedrock Nova 2 (Model: {self.model})")
        else:
            # Anthropic API setup
            self.anthropic = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-sonnet-4-20250514"
            print("✓ Using Anthropic API for AI")
    
    def fetch_jira_issue(self, issue_key: str) -> Dict[str, Any]:
        """Fetch raw JIRA issue data"""
        try:
            issue_data = self.jira_client.get_issue(issue_key)
            return issue_data
        except Exception as e:
            raise Exception(f"Failed to fetch JIRA issue {issue_key}: {str(e)}")
    
    def _extract_text_from_adf(self, content) -> str:
        """
        Extract plain text from Atlassian Document Format (ADF)
        
        Args:
            content: Can be a string, dict (ADF), or None
            
        Returns:
            Plain text string
        """
        if content is None:
            return ""
        
        if isinstance(content, str):
            return content
        
        if isinstance(content, dict):
            text_parts = []
            
            # Handle ADF structure
            if 'content' in content:
                for block in content.get('content', []):
                    block_type = block.get('type', '')
                    
                    if block_type == 'paragraph':
                        # Extract text from paragraph
                        for item in block.get('content', []):
                            if item.get('type') == 'text':
                                text_parts.append(item.get('text', ''))
                            elif item.get('type') == 'hardBreak':
                                text_parts.append('\n')
                    
                    elif block_type == 'heading':
                        # Extract heading text
                        for item in block.get('content', []):
                            if item.get('type') == 'text':
                                text_parts.append('\n' + item.get('text', '') + '\n')
                    
                    elif block_type == 'bulletList' or block_type == 'orderedList':
                        # Extract list items
                        for list_item in block.get('content', []):
                            if list_item.get('type') == 'listItem':
                                for para in list_item.get('content', []):
                                    for item in para.get('content', []):
                                        if item.get('type') == 'text':
                                            text_parts.append('• ' + item.get('text', ''))
                                text_parts.append('\n')
                    
                    elif block_type == 'codeBlock':
                        # Extract code block
                        for item in block.get('content', []):
                            if item.get('type') == 'text':
                                text_parts.append('\n```\n' + item.get('text', '') + '\n```\n')
            
            return ' '.join(text_parts).strip()
        
        # Fallback: convert to string
        return str(content)
    
    def parse_with_claude(self, raw_issue: Dict[str, Any]) -> JiraIssueDetails:
        """
        Use Claude to parse JIRA issue and extract structured information
        Focuses on extracting application URL and reproduction steps from JIRA ticket
        """
        
        print("\n" + "="*70)
        print("PARSING JIRA ISSUE WITH NOVA 2")
        print("="*70)
        
        # Extract key fields
        fields = raw_issue.get("fields", {})
        issue_key = raw_issue.get("key", "")
        
        # Extract and convert description from ADF to plain text
        raw_description = fields.get("description", "")
        description_text = self._extract_text_from_adf(raw_description)
        
        print(f"  Description type: {type(raw_description)}")
        print(f"  Description length: {len(description_text)} characters")
        
        # Try to extract application URL from JIRA first
        application_url = self.jira_client.extract_application_url(raw_issue)
        
        # Get comments for additional context
        comments = self.jira_client.get_issue_comments(issue_key)
        comments_text = "\n".join([f"- {c['author']}: {c['body']}" for c in comments[:5]])
        
        # Prepare context for Claude
        context = {
            "key": issue_key,
            "summary": fields.get("summary", ""),
            "description": description_text,  # Use converted text
            "issue_type": fields.get("issuetype", {}).get("name", ""),
            "status": fields.get("status", {}).get("name", ""),
            "priority": fields.get("priority", {}).get("name", "") if fields.get("priority") else None,
            "labels": fields.get("labels", []),
            "attachments": [att.get("content", "") for att in fields.get("attachment", [])],
            "environment": fields.get("environment", ""),
            "detected_url": application_url
        }
        
        prompt = f"""You are an expert at analyzing JIRA bug reports for automated bug reproduction.

**CRITICAL**: This system will automatically access the application URL and execute the reproduction steps.
Extract ALL necessary information from the JIRA ticket.

JIRA Issue: {issue_key}
Summary: {context['summary']}
Type: {context['issue_type']}
Status: {context['status']}

Description:
{description_text}

Environment:
{context.get('environment', 'Not specified')}

Recent Comments:
{comments_text or 'No comments'}

{f"Detected Application URL: {application_url}" if application_url else "No URL detected automatically"}

Extract the following information:

1. **Reproduction Steps**: Clear, actionable steps that can be automated
   - Include specific UI elements to interact with
   - Include specific data to enter
   - Be explicit about what to click, type, select, etc.

2. **Expected Behavior**: What should happen (the correct behavior)

3. **Actual Behavior**: What actually happens (the bug)

4. **Application Details**: 
   - **URL**: MANDATORY - Extract the application URL from description, environment, or comments
   - **name**: Application name
   - **version**: Application version if mentioned
   - **environment**: dev/staging/prod
   - **platform**: web/mobile/desktop
   - **credentials**: Any login credentials mentioned (username/password)
   - **additional_info**: Any technical details (browser, OS, etc.)

Respond in JSON format:
{{
    "reproduction_steps": [
        "Step 1: Navigate to [specific URL or page]",
        "Step 2: Click on [specific button/link]",
        "Step 3: Enter [specific data] in [specific field]",
        "..."
    ],
    "expected_behavior": "detailed expected behavior",
    "actual_behavior": "detailed actual behavior (bug)",
    "application_details": {{
        "name": "app name",
        "version": "version or null",
        "environment": "environment or null",
        "url": "MUST be a valid http/https URL",
        "platform": "web/mobile/desktop",
        "credentials": {{"username": "...", "password": "..."}},
        "additional_info": {{"browser": "Chrome", "os": "Windows", ...}}
    }}
}}

**IMPORTANT**: The URL field is MANDATORY. If not found in the ticket, return null and I will prompt for it.
Be as detailed as possible in reproduction steps - they will be executed automatically.
"""
        
        try:
            if self.use_bedrock:
                # AWS Bedrock Converse API call (correct for Nova 2)
                print(f"  📡 Calling Bedrock Converse API...")
                print(f"  Model: {self.model}")
                print(f"  Prompt length: {len(prompt)} characters")
                
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
                
                # Extract text from Converse API response
                response_text = response['output']['message']['content'][0]['text']
                print(f"  ✓ Received response from Nova 2")
                print(f"  Response length: {len(response_text)} characters")
                print(f"  Response preview: {response_text[:200]}...")
                
            else:
                print(f"  📡 Calling Anthropic API...")
                # Anthropic API call
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
            
            print(f"  🔍 Parsing JSON response...")
            
            # Try to extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                response_text = json_match.group(1)
                print(f"  ✓ Extracted JSON from code block")
            
            parsed_data = json.loads(response_text)
            print(f"  ✓ JSON parsed successfully")
            print(f"  Found {len(parsed_data.get('reproduction_steps', []))} reproduction steps")
            
            # Create ApplicationDetails with validation
            app_details_data = parsed_data.get("application_details", {})
            
            # Ensure URL is present
            app_url = app_details_data.get("url") or application_url
            if app_url:
                print(f"  ✓ Application URL: {app_url}")
            else:
                print(f"  ⚠ No application URL found in JIRA ticket!")
            
            app_details = ApplicationDetails(
                name=app_details_data.get("name") or "Unknown Application",
                version=app_details_data.get("version"),
                environment=app_details_data.get("environment") or "unknown",
                url=app_url,
                platform=app_details_data.get("platform") or "web",
                additional_info=app_details_data.get("additional_info", {})
            )
            
            # Add credentials if present
            if app_details_data.get("credentials"):
                app_details.additional_info["credentials"] = app_details_data["credentials"]
            
            # Create JiraIssueDetails with plain text description
            jira_details = JiraIssueDetails(
                issue_key=issue_key,
                summary=context["summary"],
                description=description_text,  # Use converted plain text
                issue_type=context["issue_type"],
                status=context["status"],
                priority=context["priority"],
                reproduction_steps=parsed_data.get("reproduction_steps", []),
                expected_behavior=parsed_data.get("expected_behavior"),
                actual_behavior=parsed_data.get("actual_behavior"),
                application_details=app_details,
                attachments=context["attachments"],
                labels=context["labels"]
            )
            
            print("="*70 + "\n")
            
            return jira_details
            
        except json.JSONDecodeError as e:
            print(f"  ✗ JSON PARSE ERROR: {str(e)}")
            print(f"  Response was: {response_text[:500]}")
            raise Exception(f"Failed to parse Claude response as JSON: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise Exception(f"Failed to parse JIRA issue with Claude: {str(e)}")
    
    def __call__(self, state: AgentState) -> AgentState:
        """Execute the JIRA parser node"""
        
        issue_key = state["jira_issue_key"]
        messages = state.get("messages", [])
        errors = state.get("errors", [])
        
        try:
            # Update status
            state["status"] = "fetching"
            messages.append(f"Fetching JIRA issue: {issue_key}")
            
            # Fetch raw JIRA data
            raw_data = self.fetch_jira_issue(issue_key)
            state["raw_jira_data"] = raw_data
            messages.append(f"✓ Successfully fetched JIRA issue {issue_key}")
            
            # Parse with Claude
            state["status"] = "parsing"
            messages.append("Parsing issue with Nova 2...")
            
            parsed_issue = self.parse_with_claude(raw_data)
            state["parsed_issue"] = parsed_issue.model_dump()
            
            messages.append(f"✓ Parsed {len(parsed_issue.reproduction_steps)} reproduction steps")
            messages.append(f"  Application: {parsed_issue.application_details.name or 'Not specified'}")
            messages.append(f"  Platform: {parsed_issue.application_details.platform or 'Not specified'}")
            
            if parsed_issue.application_details.url:
                messages.append(f"  🌐 Application URL: {parsed_issue.application_details.url}")
            else:
                messages.append(f"  ⚠ WARNING: No application URL found - cannot proceed with automated reproduction!")
                state["next_action"] = "abort"
                errors.append("Application URL is required but not found in JIRA ticket")
                state["messages"] = messages
                state["errors"] = errors
                return state
            
            # Set next action
            state["status"] = "parsed"
            state["next_action"] = "plan_reproduction"
            
        except Exception as e:
            state["status"] = "failed"
            error_msg = f"Error in JIRA parser: {str(e)}"
            errors.append(error_msg)
            messages.append(f"✗ {error_msg}")
            state["next_action"] = "abort"
        
        state["messages"] = messages
        state["errors"] = errors
        return state
