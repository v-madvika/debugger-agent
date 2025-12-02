"""
Simple Jira API Client (No MCP needed for POC)
"""
import requests
from requests.auth import HTTPBasicAuth
import os
from dotenv import load_dotenv

load_dotenv()

class SimpleJiraClient:
    """Direct Jira API client - no MCP server needed"""
    
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
    
    def get_issue(self, issue_key: str) -> dict:
        """Get a Jira issue"""
        url = f"{self.url}/rest/api/3/issue/{issue_key}"
        
        try:
            response = requests.get(url, auth=self.auth, headers=self.headers)
            
            # Debug: print response details
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers: {response.headers}")
            print(f"Response Text: {response.text[:500]}")  # First 500 chars
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            raise Exception(f"HTTP Error {response.status_code}: {response.text}")
        except requests.exceptions.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response: {response.text}")
        except Exception as e:
            raise Exception(f"Failed to get issue: {str(e)}")
    
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