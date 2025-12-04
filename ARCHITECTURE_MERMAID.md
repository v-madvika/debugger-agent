# Bug Reproduction Agent - Architecture Diagrams (Mermaid)

## System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI["CLI Interface\nreproduce_bug_cli.py"]
        API["Programmatic API\nBugReproductionAgent"]
    end
    
    subgraph "LangGraph Orchestration"
        STATE["Agent State\nTypedDict + Pydantic"]
        PARSER["JIRA Parser Node\njira_parser_node.py"]
        PLANNER["Planner Node\nplanner_node.py"]
        EXECUTOR["Execution Node\nexecution_node.py"]
        REPORTER["Report Node\nbug_reproduction_agent.py"]
        
        STATE --> PARSER
        PARSER --> PLANNER
        PLANNER --> EXECUTOR
        EXECUTOR --> REPORTER
    end
    
    subgraph "AI & Integration Layer"
        CLAUDE["Claude Sonnet 4.0\nAnthropic API"]
        JIRA["JIRA REST API\njira_client.py"]
        GITHUB["GitHub API\ngithub_client.py\nOptional"]
    end
    
    subgraph "Data Models"
        MODELS["Pydantic Models\nagent_state.py"]
        ISSUE[JiraIssueDetails]
        PLAN[ReproductionPlan]
        RESULT[ReproductionResult]
        
        MODELS --> ISSUE
        MODELS --> PLAN
        MODELS --> RESULT
    end
    
    subgraph "Output Layer"
        JSON["JSON Results\nresults/"]
        CONSOLE["Rich Console\nFormatted Output"]
        JIRA_COMMENT["JIRA Comments\nOptional"]
    end
    
    CLI --> STATE
    API --> STATE
    
    PARSER --> JIRA
    PARSER --> CLAUDE
    PLANNER --> CLAUDE
    EXECUTOR --> CLAUDE
    
    PARSER --> ISSUE
    PLANNER --> PLAN
    EXECUTOR --> RESULT
    
    REPORTER --> JSON
    REPORTER --> CONSOLE
    REPORTER --> JIRA_COMMENT
    
    GITHUB -.-> PLANNER
    
    style CLAUDE fill:#f9f,stroke:#333,stroke-width:4px
    style STATE fill:#bbf,stroke:#333,stroke-width:2px
    style MODELS fill:#bfb,stroke:#333,stroke-width:2px
```

## LangGraph Workflow

```mermaid
stateDiagram-v2
    [*] --> Initializing
    
    Initializing --> FetchParse: Start Workflow
    
    FetchParse --> Parsing: Fetch from JIRA
    Parsing --> Parsed: Claude Analysis
    
    Parsed --> Planning: Success
    Parsed --> Failed: Error
    
    Planning --> Planned: Create Plan
    Planning --> Failed: Error
    
    Planned --> Executing: Start Execution
    
    Executing --> Analyzing: Simulate Steps
    Analyzing --> Completed: Analysis Done
    Executing --> Failed: Error
    
    Completed --> Reporting: Generate Report
    
    Reporting --> [*]: Done
    Failed --> [*]: Abort
    
    note right of FetchParse
        JiraParserNode
        - Fetch issue
        - Extract data
    end note
    
    note right of Planning
        PlannerNode
        - Analyze issue
        - Create steps
    end note
    
    note right of Executing
        ExecutionNode
        - Simulate steps
        - Capture results
    end note
    
    note right of Reporting
        ReportNode
        - Format output
        - Save results
    end note
```

## Node Architecture

```mermaid
graph LR
    subgraph "JIRA Parser Node"
        INPUT1[Input: issue_key]
        FETCH[Fetch from JIRA API]
        PARSE[Parse with Claude]
        OUTPUT1[Output: JiraIssueDetails]
        
        INPUT1 --> FETCH
        FETCH --> PARSE
        PARSE --> OUTPUT1
    end
    
    subgraph "Planner Node"
        INPUT2["Input: JiraIssueDetails\n+ code_files"]
        ANALYZE["Analyze Issue"]
        CREATE["Create Plan\nwith Claude"]
        VALIDATE[Validate Plan]
        OUTPUT2[Output: ReproductionPlan]
        
        INPUT2 --> ANALYZE
        ANALYZE --> CREATE
        CREATE --> VALIDATE
        VALIDATE --> OUTPUT2
    end
    
    subgraph "Execution Node"
        INPUT3[Input: ReproductionPlan]
        LOOP[For Each Step]
        SIMULATE[Simulate with Claude]
        CAPTURE[Capture Result]
        FINAL[Analyze All Results]
        OUTPUT3[Output: ReproductionResult]
        
        INPUT3 --> LOOP
        LOOP --> SIMULATE
        SIMULATE --> CAPTURE
        CAPTURE --> LOOP
        LOOP --> FINAL
        FINAL --> OUTPUT3
    end
    
    OUTPUT1 --> INPUT2
    OUTPUT2 --> INPUT3
```

## Data Flow

```mermaid
flowchart TD
    START([User: Issue Key])
    
    subgraph "Stage 1: Fetch & Parse"
        JIRA_API["JIRA REST API"]
        CLAUDE1["Claude: Extract Structure"]
        ISSUE_DATA["JiraIssueDetails\n- Reproduction steps\n- Expected/Actual behavior\n- App details"]
    end
    
    subgraph "Stage 2: Planning"
        CODE["Code Files\nOptional"]
        CLAUDE2["Claude: Create Plan"]
        PLAN_DATA["ReproductionPlan\n- Prerequisites\n- Environment setup\n- Atomic steps"]
    end
    
    subgraph "Stage 3: Execution"
        CLAUDE3["Claude: Simulate Steps"]
        STEP_RESULTS["Step Results\n- Status\n- Actual outcomes\n- Errors"]
        CLAUDE4["Claude: Analyze"]
        FINAL_RESULT["ReproductionResult\n- Bug reproduced?\n- Root cause\n- Recommendations"]
    end
    
    subgraph "Stage 4: Output"
        JSON_FILE["JSON File\nresults/*.json"]
        CLI_OUTPUT["Rich CLI Output\nFormatted Report"]
        JIRA_POST["JIRA Comment\nOptional"]
    end
    
    START --> JIRA_API
    JIRA_API --> CLAUDE1
    CLAUDE1 --> ISSUE_DATA
    
    ISSUE_DATA --> CLAUDE2
    CODE -.-> CLAUDE2
    CLAUDE2 --> PLAN_DATA
    
    PLAN_DATA --> CLAUDE3
    CLAUDE3 --> STEP_RESULTS
    STEP_RESULTS --> CLAUDE4
    CLAUDE4 --> FINAL_RESULT
    
    FINAL_RESULT --> JSON_FILE
    FINAL_RESULT --> CLI_OUTPUT
    FINAL_RESULT --> JIRA_POST
    
    style CLAUDE1 fill:#f9f
    style CLAUDE2 fill:#f9f
    style CLAUDE3 fill:#f9f
    style CLAUDE4 fill:#f9f
```

## Class Diagram

```mermaid
classDiagram
    class BugReproductionAgent {
        +jira_client: SimpleJiraClient
        +jira_parser: JiraParserNode
        +planner: ReproductionPlannerNode
        +executor: ExecutionNode
        +workflow: StateGraph
        +app: CompiledGraph
        +reproduce_bug(issue_key, code_files) Dict
        +get_workflow_diagram() str
        -_build_workflow() StateGraph
        -_route_after_parse(state) str
        -_generate_report(state) AgentState
    }
    
    class AgentState {
        <<TypedDict>>
        +jira_issue_key: str
        +raw_jira_data: Dict
        +parsed_issue: JiraIssueDetails
        +reproduction_plan: ReproductionPlan
        +current_step: int
        +reproduction_result: ReproductionResult
        +messages: List[str]
        +errors: List[str]
        +status: str
        +code_files: Dict[str, str]
    }
    
    class JiraIssueDetails {
        <<Pydantic>>
        +issue_key: str
        +summary: str
        +description: str
        +issue_type: str
        +status: str
        +reproduction_steps: List[str]
        +expected_behavior: str
        +actual_behavior: str
        +application_details: ApplicationDetails
    }
    
    class ReproductionPlan {
        <<Pydantic>>
        +issue_key: str
        +reproduction_steps: List[ReproductionStep]
        +prerequisites: List[str]
        +environment_setup: Dict
        +expected_outcome: str
    }
    
    class ReproductionStep {
        <<Pydantic>>
        +step_number: int
        +description: str
        +action: str
        +target: str
        +expected_result: str
        +actual_result: str
        +status: str
        +error: str
    }
    
    class ReproductionResult {
        <<Pydantic>>
        +issue_key: str
        +bug_reproduced: bool
        +executed_steps: List[ReproductionStep]
        +screenshots: List[str]
        +logs: List[str]
        +root_cause_analysis: str
        +recommendations: List[str]
        +confidence_score: float
    }
    
    class JiraParserNode {
        +anthropic: Anthropic
        +jira_client: SimpleJiraClient
        +fetch_jira_issue(issue_key) Dict
        +parse_with_claude(raw_issue) JiraIssueDetails
        +__call__(state) AgentState
    }
    
    class ReproductionPlannerNode {
        +anthropic: Anthropic
        +create_reproduction_plan(issue_details, code_files) ReproductionPlan
        +validate_plan(plan) List[str]
        +__call__(state) AgentState
    }
    
    class ExecutionNode {
        +anthropic: Anthropic
        +simulate_step_execution(step, context) ReproductionStep
        +analyze_reproduction_results(plan, steps, context) ReproductionResult
        +__call__(state) AgentState
    }
    
    BugReproductionAgent --> JiraParserNode
    BugReproductionAgent --> ReproductionPlannerNode
    BugReproductionAgent --> ExecutionNode
    BugReproductionAgent --> AgentState
    
    AgentState --> JiraIssueDetails
    AgentState --> ReproductionPlan
    AgentState --> ReproductionResult
    
    ReproductionPlan --> ReproductionStep
    ReproductionResult --> ReproductionStep
    
    JiraParserNode ..> JiraIssueDetails : creates
    ReproductionPlannerNode ..> ReproductionPlan : creates
    ExecutionNode ..> ReproductionResult : creates
```

## Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI Interface
    participant Agent as BugReproductionAgent
    participant Parser as JiraParserNode
    participant Planner as PlannerNode
    participant Executor as ExecutionNode
    participant Claude as Claude Sonnet 4.0
    participant JIRA as JIRA API
    
    User->>CLI: reproduce_bug_cli.py KAN-4
    CLI->>Agent: reproduce_bug("KAN-4")
    
    Agent->>Parser: fetch_and_parse(state)
    Parser->>JIRA: get_issue("KAN-4")
    JIRA-->>Parser: raw_issue_data
    
    Parser->>Claude: parse issue (prompt)
    Claude-->>Parser: structured_data
    Parser-->>Agent: JiraIssueDetails
    
    Agent->>Planner: create_plan(state)
    Planner->>Claude: create reproduction plan
    Claude-->>Planner: reproduction_plan
    Planner-->>Agent: ReproductionPlan
    
    Agent->>Executor: execute(state)
    
    loop For each step
        Executor->>Claude: simulate_step_execution
        Claude-->>Executor: step_result
    end
    
    Executor->>Claude: analyze_reproduction_results
    Claude-->>Executor: root_cause + recommendations
    Executor-->>Agent: ReproductionResult
    
    Agent->>Agent: generate_report(state)
    Agent-->>CLI: final_state
    CLI-->>User: Display results + save JSON
    
    opt Auto-post enabled
        Agent->>JIRA: add_comment(result)
    end
```

## Component Interaction

```mermaid
graph TB
    subgraph "External Services"
        JIRA_SVC["JIRA Cloud\nAtlassian"]
        ANTHROPIC_SVC["Anthropic API\nClaude Sonnet 4.0"]
        GITHUB_SVC["GitHub API\nOptional"]
    end
    
    subgraph "Application Layer"
        CLI_APP["CLI Application\nRich Interface"]
        AGENT_APP["Agent Core\nLangGraph Workflow"]
    end
    
    subgraph "Business Logic"
        PARSER_LOGIC["JIRA Parser\nExtract & Structure"]
        PLANNER_LOGIC["Reproduction Planner\nStrategy Creation"]
        EXECUTOR_LOGIC["Execution Engine\nSimulation & Analysis"]
    end
    
    subgraph "Data Layer"
        STATE_MGMT["State Management\nLangGraph State"]
        MODELS_LAYER["Pydantic Models\nType Safety"]
        PERSISTENCE["JSON Storage\nresults/"]
    end
    
    subgraph "Infrastructure"
        ENV_CONFIG["Environment Config\n.env"]
        LOGGING["Logging & Errors\nConsole Output"]
    end
    
    CLI_APP --> AGENT_APP
    AGENT_APP --> PARSER_LOGIC
    AGENT_APP --> PLANNER_LOGIC
    AGENT_APP --> EXECUTOR_LOGIC
    
    PARSER_LOGIC --> JIRA_SVC
    PARSER_LOGIC --> ANTHROPIC_SVC
    PLANNER_LOGIC --> ANTHROPIC_SVC
    EXECUTOR_LOGIC --> ANTHROPIC_SVC
    PLANNER_LOGIC -.-> GITHUB_SVC
    
    PARSER_LOGIC --> STATE_MGMT
    PLANNER_LOGIC --> STATE_MGMT
    EXECUTOR_LOGIC --> STATE_MGMT
    
    STATE_MGMT --> MODELS_LAYER
    AGENT_APP --> PERSISTENCE
    
    ENV_CONFIG --> JIRA_SVC
    ENV_CONFIG --> ANTHROPIC_SVC
    ENV_CONFIG --> GITHUB_SVC
    
    AGENT_APP --> LOGGING
    
    style ANTHROPIC_SVC fill:#f9f,stroke:#333,stroke-width:3px
    style AGENT_APP fill:#bbf,stroke:#333,stroke-width:2px
    style MODELS_LAYER fill:#bfb,stroke:#333,stroke-width:2px
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development Environment"
        DEV_CLI["Local CLI\nDeveloper Machine"]
        DEV_ENV[".env Configuration\nAPI Keys"]
    end
    
    subgraph "CI/CD Pipeline"
        GH_ACTIONS["GitHub Actions\nAutomated Testing"]
        AUTO_REPRO["Automated Reproduction\nOn Issue Creation"]
    end
    
    subgraph "Production Usage"
        PROD_CLI["Production CLI\nQA/Dev Teams"]
        BATCH_PROC["Batch Processing\nMultiple Issues"]
        API_INTEG["API Integration\nOther Systems"]
    end
    
    subgraph "External Services"
        JIRA_PROD["JIRA Production"]
        ANTHROPIC_PROD["Anthropic API"]
    end
    
    subgraph "Output & Storage"
        JSON_STORAGE["JSON Results\nHistorical Data"]
        JIRA_COMMENTS["JIRA Comments\nAutomated Feedback"]
        DASHBOARDS["Analytics Dashboard\nFuture"]
    end
    
    DEV_CLI --> DEV_ENV
    DEV_CLI --> JIRA_PROD
    DEV_CLI --> ANTHROPIC_PROD
    
    GH_ACTIONS --> AUTO_REPRO
    AUTO_REPRO --> JIRA_PROD
    AUTO_REPRO --> ANTHROPIC_PROD
    
    PROD_CLI --> JIRA_PROD
    BATCH_PROC --> JIRA_PROD
    API_INTEG --> JIRA_PROD
    
    PROD_CLI --> ANTHROPIC_PROD
    BATCH_PROC --> ANTHROPIC_PROD
    API_INTEG --> ANTHROPIC_PROD
    
    DEV_CLI --> JSON_STORAGE
    PROD_CLI --> JSON_STORAGE
    BATCH_PROC --> JSON_STORAGE
    
    AUTO_REPRO --> JIRA_COMMENTS
    API_INTEG --> JIRA_COMMENTS
    
    JSON_STORAGE -.-> DASHBOARDS
```

