from pydantic import BaseModel, field_validator
from typing import Union, Any

class JiraIssueDetails(BaseModel):
    # ...existing code...
    description: str
    # ...existing code...
    
    @field_validator('description', mode='before')
    @classmethod
    def normalize_description(cls, v: Any) -> str:
        """Convert description to string if it's a dict or other type."""
        if isinstance(v, dict):
            # Handle Atlassian Document Format (ADF)
            if 'content' in v:
                return cls._extract_text_from_adf(v)
            # Handle other dict formats
            return str(v)
        if isinstance(v, list):
            return ' '.join(str(item) for item in v)
        return str(v) if v is not None else ""
    
    @staticmethod
    def _extract_text_from_adf(adf: dict) -> str:
        """Extract plain text from Atlassian Document Format."""
        text_parts = []
        
        def extract_text(node: dict):
            if isinstance(node, dict):
                if node.get('type') == 'text':
                    text_parts.append(node.get('text', ''))
                if 'content' in node:
                    for child in node['content']:
                        extract_text(child)
        
        extract_text(adf)
        return ' '.join(text_parts).strip()