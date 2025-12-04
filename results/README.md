# Results Directory

This directory contains the output from bug reproduction attempts.

## File Format

Each reproduction run creates a JSON file named: `<ISSUE-KEY>_result.json`

Example: `KAN-4_result.json`

## JSON Structure

```json
{
  "jira_issue_key": "KAN-4",
  "status": "completed",
  "parsed_issue": {
    "issue_key": "KAN-4",
    "summary": "Bug summary here",
    "issue_type": "Bug",
    "reproduction_steps": [
      "Step 1",
      "Step 2"
    ],
    "expected_behavior": "What should happen",
    "actual_behavior": "What actually happens",
    "application_details": {
      "name": "App Name",
      "version": "1.0.0",
      "environment": "production",
      "platform": "web"
    }
  },
  "reproduction_plan": {
    "issue_key": "KAN-4",
    "reproduction_steps": [...],
    "prerequisites": [...],
    "environment_setup": {},
    "expected_outcome": "..."
  },
  "reproduction_result": {
    "issue_key": "KAN-4",
    "bug_reproduced": true,
    "confidence_score": 0.85,
    "root_cause_analysis": "Detailed analysis...",
    "recommendations": [
      "Recommendation 1",
      "Recommendation 2"
    ],
    "executed_steps": [
      {
        "step_number": 1,
        "description": "...",
        "action": "navigate",
        "status": "success",
        "expected_result": "...",
        "actual_result": "..."
      }
    ]
  },
  "messages": [...],
  "errors": []
}
```

## Usage

### Load Results Programmatically

```python
import json

# Load result
with open('results/KAN-4_result.json', 'r') as f:
    result = json.load(f)

# Access data
bug_reproduced = result['reproduction_result']['bug_reproduced']
confidence = result['reproduction_result']['confidence_score']
root_cause = result['reproduction_result']['root_cause_analysis']

print(f"Bug reproduced: {bug_reproduced}")
print(f"Confidence: {confidence:.0%}")
print(f"Root cause: {root_cause}")
```

### Query Multiple Results

```python
import json
from pathlib import Path

# Load all results
results_dir = Path('results')
all_results = []

for json_file in results_dir.glob('*.json'):
    with open(json_file, 'r') as f:
        all_results.append(json.load(f))

# Find reproduced bugs
reproduced = [
    r for r in all_results 
    if r.get('reproduction_result', {}).get('bug_reproduced')
]

print(f"Found {len(reproduced)} reproduced bugs out of {len(all_results)} total")
```

### Generate Report

```python
import json
from pathlib import Path

results_dir = Path('results')

for json_file in results_dir.glob('*.json'):
    with open(json_file, 'r') as f:
        result = json.load(f)
    
    issue_key = result['jira_issue_key']
    repro_result = result.get('reproduction_result', {})
    
    print(f"\n{issue_key}:")
    print(f"  Reproduced: {repro_result.get('bug_reproduced', False)}")
    print(f"  Confidence: {repro_result.get('confidence_score', 0):.0%}")
    print(f"  Recommendations: {len(repro_result.get('recommendations', []))}")
```

## Cleaning Up

To remove old results:

```bash
# Remove all results
rm results/*.json

# Remove specific result
rm results/KAN-4_result.json

# Remove results older than 7 days (Linux/Mac)
find results -name "*.json" -mtime +7 -delete
```

## Integration

### CI/CD

```yaml
# Example GitHub Actions workflow
- name: Run Bug Reproduction
  run: |
    cd agent
    python reproduce_bug_cli.py ${{ github.event.issue.key }}
    
- name: Upload Results
  uses: actions/upload-artifact@v3
  with:
    name: reproduction-results
    path: results/*.json
```

### Analysis Pipeline

```python
# Aggregate results for analysis
import json
from pathlib import Path
import pandas as pd

results = []
for json_file in Path('results').glob('*.json'):
    with open(json_file, 'r') as f:
        data = json.load(f)
        results.append({
            'issue_key': data['jira_issue_key'],
            'reproduced': data['reproduction_result']['bug_reproduced'],
            'confidence': data['reproduction_result']['confidence_score'],
            'steps': len(data['reproduction_result']['executed_steps'])
        })

df = pd.DataFrame(results)
print(df.describe())
```

## Notes

- Results are automatically saved after each reproduction run
- Files are overwritten if you run the same issue multiple times
- Results include full state for debugging and analysis
- JSON format allows easy integration with other tools
