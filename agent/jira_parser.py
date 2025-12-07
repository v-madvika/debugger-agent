import os
import json
import logging
import sys
from typing import Union, Dict, Any
from .models import JiraIssueDetails
from .bedrock_client import BedrockClient

# Configure logging with console handler
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Add console handler if not already present
if not logger.handlers:
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s [%(levelname)8s] %(name)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

# Also add print statements for immediate visibility
def log_and_print(level: str, message: str):
    """Log and print message for visibility"""
    print(f"[{level}] {message}")
    if level == "INFO":
        logger.info(message)
    elif level == "DEBUG":
        logger.debug(message)
    elif level == "ERROR":
        logger.error(message)
    elif level == "WARNING":
        logger.warning(message)

def parse_jira_issue_with_claude(raw_issue: dict) -> JiraIssueDetails:
    """Parse JIRA issue using AI model to extract structured data."""
    log_and_print("INFO", "=== parse_jira_issue_with_claude: Starting ===")
    log_and_print("DEBUG", f"Raw issue keys: {list(raw_issue.keys())}")
    
    try:
        # Pre-process description if it's in ADF format
        description = raw_issue.get('fields', {}).get('description')
        log_and_print("INFO", f"Description type: {type(description)}")
        
        if isinstance(description, dict):
            log_and_print("INFO", "Description is dict (ADF format), extracting text...")
            description = extract_description_text(description)
            raw_issue['fields']['description'] = description
            log_and_print("INFO", f"Extracted description length: {len(description)}")
        
        # Create prompt for the model
        system_prompt = """You are a JIRA issue parser. Extract structured information from the JIRA issue data.
Return ONLY valid JSON matching the JiraIssueDetails schema. Do not include any explanations or markdown formatting."""
        
        prompt = f"""Parse this JIRA issue and return JSON with these fields:
- key: issue key
- summary: issue title
- description: issue description (plain text)
- status: current status
- priority: priority level
- assignee: assigned user (or null)
- reporter: reporter user
- issue_type: type of issue

JIRA Issue Data:
{json.dumps(raw_issue, indent=2)}

Return only the JSON object, no other text."""
        
        log_and_print("INFO", "Calling bedrock_client.invoke_model()...")
        log_and_print("DEBUG", f"Prompt length: {len(prompt)}")
        
        # Invoke model
        response_text = bedrock_client.invoke_model(prompt, system_prompt)
        
        log_and_print("INFO", f"✓ Received response from model (length: {len(response_text)})")
        log_and_print("DEBUG", f"Response preview: {response_text[:200]}")
        
        # Parse response
        response_text = response_text.strip()
        if response_text.startswith('{') and response_text.endswith('}'):
            response_json = json.loads(response_text)
            log_and_print("INFO", f"✓ Parsed JSON response successfully")
            log_and_print("DEBUG", f"Response JSON: {json.dumps(response_json, indent=2)}")
            return JiraIssueDetails(**response_json)
        else:
            error_msg = f"Invalid JSON response: {response_text[:200]}"
            log_and_print("ERROR", error_msg)
            raise ValueError(error_msg)
            
    except Exception as e:
        # Handle and log the exception
        log_and_print("ERROR", f"✗ Error parsing JIRA issue: {str(e)}")
        logger.error(f"Full exception:", exc_info=True)
        print(f"EXCEPTION DETAILS: {type(e).__name__}: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return JiraIssueDetails()  # Return empty details on error

def extract_description_text(description: Union[str, dict]) -> str:
    """Extract plain text from JIRA description (handles ADF format)."""
    if isinstance(description, str):
        return description
    
    if isinstance(description, dict):
        # Handle Atlassian Document Format
        if 'content' in description:
            text_parts = []
            for content in description.get('content', []):
                if content.get('type') == 'paragraph':
                    for item in content.get('content', []):
                        if item.get('type') == 'text':
                            text_parts.append(item.get('text', ''))
            return ' '.join(text_parts)
    
    return str(description)

def parse_with_claude(issue_data: Dict) -> Dict:
    """Parse JIRA issue using Claude with detailed logging"""
    
    log_and_print("INFO", "="*70)
    log_and_print("INFO", "JIRA PARSER - PARSE WITH CLAUDE")
    log_and_print("INFO", "="*70)
    log_and_print("INFO", f"Issue Key: {issue_data.get('key', 'UNKNOWN')}")
    log_and_print("DEBUG", f"Issue data keys: {list(issue_data.keys())}")
    
    try:
        # Create prompt
        prompt = _create_parsing_prompt(issue_data)
        
        log_and_print("INFO", f"Prompt created, length: {len(prompt)} characters")
        log_and_print("DEBUG", f"Full prompt:\n{prompt}")
        
        # Invoke LLM with logging
        if hasattr(llm, '_invoke_llm_with_logging'):
            response_text = llm._invoke_llm_with_logging(
                prompt, 
                context="JIRA Issue Parsing"
            )
        else:
            log_and_print("INFO", "Using standard LLM invoke (no custom logging)")
            response = llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
        
        log_and_print("INFO", "✓ Parsing LLM response completed")
        # ...existing code to parse response...
        
    except Exception as e:
        log_and_print("ERROR", f"✗ Error in JIRA parser: {str(e)}")
        logger.error("Full exception:", exc_info=True)
        raise