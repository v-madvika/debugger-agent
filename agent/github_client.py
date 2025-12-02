"""
Simple GitHub API Client
"""
import os
from github import Github
from github.GithubException import BadCredentialsException
from dotenv import load_dotenv

load_dotenv()

class SimpleGitHubClient:
    """Direct GitHub API client"""
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.owner = os.getenv("GITHUB_OWNER")
        self.repo_name = os.getenv("GITHUB_REPO")
        
        if not all([self.token, self.owner, self.repo_name]):
            raise ValueError(
                "Missing GitHub configuration. Please set GITHUB_TOKEN, "
                "GITHUB_OWNER, and GITHUB_REPO in your .env file"
            )
        
        try:
            self.github = Github(self.token)
            # Test authentication
            self.github.get_user().login
            self.repo = self.github.get_repo(f"{self.owner}/{self.repo_name}")
        except BadCredentialsException:
            raise ValueError(
                "Invalid GitHub token. Please check your GITHUB_TOKEN in .env\n"
                "To create a new token:\n"
                "1. Go to https://github.com/settings/tokens\n"
                "2. Click 'Generate new token (classic)'\n"
                "3. Select scopes: 'repo' (full control)\n"
                "4. Copy the token and update GITHUB_TOKEN in .env"
            )
        except Exception as e:
            raise ValueError(f"GitHub connection failed: {str(e)}")
    
    def get_file_content(self, file_path: str) -> str:
        """Get file content"""
        content = self.repo.get_contents(file_path)
        return content.decoded_content.decode('utf-8')
    
    def search_code(self, query: str) -> list:
        """Search code in repository"""
        query_str = f"{query} repo:{self.owner}/{self.repo_name}"
        results = self.github.search_code(query_str)
        return [{"path": r.path, "score": r.score} for r in results[:10]]
    
    def get_recent_commits(self, count: int = 10) -> list:
        """Get recent commits"""
        commits = self.repo.get_commits()[:count]
        return [{
            "sha": c.sha[:7],
            "message": c.commit.message,
            "author": c.commit.author.name,
            "date": c.commit.author.date.isoformat()
        } for c in commits]