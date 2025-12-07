"""
Agent State and Schema Definitions for Bug Reproduction Agent
"""
from typing import TypedDict, List, Dict, Any, Optional, Annotated, Union
from pydantic import BaseModel, Field, field_validator
import operator


class ReproductionStep(BaseModel):
    """Single step in bug reproduction"""
    step_number: int = Field(description="Step number in sequence")
    description: str = Field(description="Description of the step")
    action: str = Field(description="Action to perform (e.g., 'navigate', 'click', 'input', 'verify')")
    target: Optional[str] = Field(default=None, description="Target element or location")
    expected_result: Optional[str] = Field(default=None, description="Expected outcome")
    actual_result: Optional[str] = Field(default=None, description="Actual outcome after execution")
    status: str = Field(default="pending", description="Status: pending, success, failed, skipped")
    error: Optional[str] = Field(default=None, description="Error message if failed")


class ApplicationDetails(BaseModel):
    """Application details from JIRA"""
    name: Optional[str] = Field(default=None, description="Application name")
    version: Optional[str] = Field(default=None, description="Application version")
    environment: Optional[str] = Field(default=None, description="Environment (dev, staging, prod)")
    url: Optional[str] = Field(default=None, description="Application URL")
    platform: Optional[str] = Field(default=None, description="Platform (web, mobile, desktop)")
    additional_info: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class JiraIssueDetails(BaseModel):
    """Structured JIRA issue details"""
    issue_key: str
    summary: str
    description: Union[str, Dict[str, Any]] = ""  # Allow both string and ADF dict
    issue_type: str = "Bug"
    status: str = "Open"
    priority: Optional[str] = None
    reproduction_steps: List[str] = Field(default_factory=list, description="Steps to reproduce")
    expected_behavior: Optional[str] = Field(default=None, description="Expected behavior")
    actual_behavior: Optional[str] = Field(default=None, description="Actual behavior")
    application_details: Optional[ApplicationDetails] = Field(default=None, description="Application details")
    attachments: List[str] = Field(default_factory=list, description="Attachment URLs")
    labels: List[str] = Field(default_factory=list, description="Issue labels")
    
    @field_validator('description')
    @classmethod
    def convert_description_to_string(cls, v):
        """Convert ADF description to plain text if needed"""
        if isinstance(v, dict):
            # Simple ADF to text conversion
            text_parts = []
            if 'content' in v:
                for block in v.get('content', []):
                    if block.get('type') == 'paragraph':
                        for item in block.get('content', []):
                            if item.get('type') == 'text':
                                text_parts.append(item.get('text', ''))
            return ' '.join(text_parts)
        return v if isinstance(v, str) else str(v)


class ReproductionPlan(BaseModel):
    """Plan for reproducing the bug"""
    issue_key: str = Field(description="JIRA issue key")
    reproduction_steps: List[ReproductionStep] = Field(description="Detailed reproduction steps")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites before reproduction")
    environment_setup: Dict[str, Any] = Field(default_factory=dict, description="Environment setup requirements")
    expected_outcome: str = Field(description="Expected outcome of reproduction")


class ReproductionResult(BaseModel):
    """Result of bug reproduction attempt"""
    issue_key: str = Field(description="JIRA issue key")
    bug_reproduced: bool = Field(description="Whether bug was successfully reproduced")
    executed_steps: List[ReproductionStep] = Field(description="Steps that were executed")
    screenshots: List[str] = Field(default_factory=list, description="Screenshot paths")
    logs: List[str] = Field(default_factory=list, description="Log entries")
    root_cause_analysis: Optional[str] = Field(default=None, description="Potential root cause")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for fix")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in reproduction (0-1)")


class AgentState(TypedDict):
    """Main state for the LangGraph agent"""
    # Input
    jira_issue_key: str
    
    # JIRA data
    raw_jira_data: Optional[Dict[str, Any]]
    parsed_issue: Optional[JiraIssueDetails]
    
    # Planning
    reproduction_plan: Optional[ReproductionPlan]
    
    # Execution
    current_step: int
    reproduction_result: Optional[ReproductionResult]
    
    # Messages and context
    messages: Annotated[List[str], operator.add]
    errors: Annotated[List[str], operator.add]
    
    # Status tracking
    status: str  # "fetching", "parsing", "planning", "executing", "completed", "failed"
    next_action: Optional[str]
    
    # Additional context
    code_files: Dict[str, str]  # filename: content
    github_commits: List[Dict[str, Any]]
    related_issues: List[str]


class NodeOutput(BaseModel):
    """Standard output from each node"""
    success: bool = Field(description="Whether node execution was successful")
    message: str = Field(description="Status message")
    updates: Dict[str, Any] = Field(default_factory=dict, description="State updates to apply")
    next_node: Optional[str] = Field(default=None, description="Next node to execute")
