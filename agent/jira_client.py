"""
Enhanced Jira API Client with comprehensive REST API support
Focuses on extracting application details and bug reproduction information
"""
import requests
from requests.auth import HTTPBasicAuth
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
import json

load_dotenv()

class SimpleJiraClient:
    """
    Enhanced JIRA REST API client for bug reproduction
    All application and bug details are fetched from JIRA tickets
    """
    
    def __init__(self):
        self.url = os.getenv("JIRA_URL")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.project_key = os.getenv("JIRA_PROJECT_KEY")
        
        # Ensure URL has https://
        if not self.url.startswith("http"):
            self.url = f"https://{self.url}"
        
        # Remove trailing slash if present
        self.url = self.url.rstrip('/')
        
        if not all([self.url, self.email, self.api_token]):
            raise ValueError("Missing Jira configuration in .env file")
        
        self.auth = (self.email, self.api_token)
        self.headers = {"Accept": "application/json"}
        
        print(f"✓ JIRA Client initialized: {self.url}")
        print(f"✓ Project: {self.project_key}")
    
    def get_issue(self, issue_key: str, expand: List[str] = None) -> Dict[str, Any]:
        """
        Get a comprehensive JIRA issue with all details
        
        Args:
            issue_key: JIRA issue key (e.g., 'KAN-4')
            expand: List of fields to expand (comments, attachments, etc.)
        
        Returns:
            Complete JIRA issue data including custom fields
        """
        expand_params = expand or ["renderedFields", "names", "schema", "transitions"]
        url = f"{self.url}/rest/api/3/issue/{issue_key}"
        
        try:
            params = {"expand": ",".join(expand_params)}
            response = requests.get(url, auth=self.auth, headers=self.headers, params=params)
            
            print(f"✓ Fetching JIRA issue: {issue_key}")
            print(f"  Status Code: {response.status_code}")
            
            response.raise_for_status()
            issue_data = response.json()
            
            # Log key information
            fields = issue_data.get("fields", {})
            print(f"  Summary: {fields.get('summary', 'N/A')}")
            print(f"  Type: {fields.get('issuetype', {}).get('name', 'N/A')}")
            print(f"  Status: {fields.get('status', {}).get('name', 'N/A')}")
            
            return issue_data
            
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP Error {response.status_code}: {response.text}")
        except requests.exceptions.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {response.text}")
        except Exception as e:
            raise Exception(f"Failed to get issue {issue_key}: {str(e)}")
    
    def search_issues(self, jql: str, max_results: int = 10) -> dict:
        """Search issues with JQL"""
        url = f"{self.url}/rest/api/3/search"
        response = requests.get(
            url,
            auth=self.auth,
            headers=self.headers,
            params={"jql": jql, "maxResults": max_results}
        )
        response.raise_for_status()
        return response.json()
    
    def add_comment(self, issue_key: str, comment: str) -> dict:
        """Add comment to issue"""
        url = f"{self.url}/rest/api/3/issue/{issue_key}/comment"
        body = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [{
                    "type": "paragraph",
                    "content": [{"type": "text", "text": comment}]
                }]
            }
        }
        response = requests.post(
            url,
            auth=self.auth,
            headers={**self.headers, "Content-Type": "application/json"},
            json=body
        )
        response.raise_for_status()
        return response.json()
    
    def get_open_bugs(self, max_results: int = 20) -> dict:
        """Get open bugs"""
        jql = f"project = {self.project_key} AND issuetype = Bug AND status != Done"
        return self.search_issues(jql, max_results)
    
    def get_all_issues(self, max_results: int = 50) -> dict:
        """Get all issues in the project"""
        jql = f"project = {self.project_key} ORDER BY created DESC"
        return self.search_issues(jql, max_results)
    
    def get_issue_attachments(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get all attachments for a JIRA issue
        
        Returns:
            List of attachment metadata (filename, URL, content-type, size)
        """
        issue = self.get_issue(issue_key)
        attachments = issue.get("fields", {}).get("attachment", [])
        
        attachment_list = []
        for att in attachments:
            attachment_list.append({
                "filename": att.get("filename"),
                "url": att.get("content"),
                "mimeType": att.get("mimeType"),
                "size": att.get("size"),
                "created": att.get("created")
            })
        
        return attachment_list
    
    def get_issue_comments(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get all comments for a JIRA issue
        
        Returns:
            List of comments with author, body, and timestamp
        """
        url = f"{self.url}/rest/api/3/issue/{issue_key}/comment"
        
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            comments = []
            
            for comment in data.get("comments", []):
                comments.append({
                    "author": comment.get("author", {}).get("displayName"),
                    "body": comment.get("body"),
                    "created": comment.get("created"),
                    "updated": comment.get("updated")
                })
            
            return comments
            
        except Exception as e:
            print(f"⚠ Failed to fetch comments: {str(e)}")
            return []
    
    def get_issue_transitions(self, issue_key: str) -> List[Dict[str, Any]]:
        """
        Get available transitions for a JIRA issue
        
        Returns:
            List of possible status transitions
        """
        url = f"{self.url}/rest/api/3/issue/{issue_key}/transitions"
        
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("transitions", [])
            
        except Exception as e:
            print(f"⚠ Failed to fetch transitions: {str(e)}")
            return []
    
    def transition_issue(self, issue_key: str, transition_id: str) -> bool:
        """
        Transition a JIRA issue to a new status
        
        Args:
            issue_key: JIRA issue key
            transition_id: ID of the transition to execute
        
        Returns:
            True if successful
        """
        url = f"{self.url}/rest/api/3/issue/{issue_key}/transitions"
        
        body = {
            "transition": {"id": transition_id}
        }
        
        try:
            response = requests.post(
                url,
                auth=self.auth,
                headers={**self.headers, "Content-Type": "application/json"},
                json=body
            )
            response.raise_for_status()
            return True
            
        except Exception as e:
            print(f"⚠ Failed to transition issue: {str(e)}")
            return False
    
    def extract_application_url(self, issue_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract application URL from JIRA issue description or custom fields
        
        Looks for:
        - Custom fields named 'Application URL', 'App URL', 'URL'
        - URLs in description text
        - Environment field with URL
        
        Returns:
            Application URL if found, None otherwise
        """
        fields = issue_data.get("fields", {})
        
        # Check description for URLs
        description = fields.get("description", "")
        if description:
            # Extract URLs from description text
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
            urls = re.findall(url_pattern, str(description))
            if urls:
                print(f"  Found URL in description: {urls[0]}")
                return urls[0]
        
        # Check custom fields
        for field_key, field_value in fields.items():
            if field_value and isinstance(field_value, str):
                if any(keyword in field_key.lower() for keyword in ['url', 'link', 'application']):
                    import re
                    urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', field_value)
                    if urls:
                        print(f"  Found URL in field {field_key}: {urls[0]}")
                        return urls[0]
        
        # Check environment field
        environment = fields.get("environment", "")
        if environment:
            import re
            urls = re.findall(r'https?://[^\s<>"{}|\\^`\[\]]+', str(environment))
            if urls:
                print(f"  Found URL in environment: {urls[0]}")
                return urls[0]
        
        return None