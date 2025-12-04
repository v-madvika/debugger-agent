# Convert Mermaid Diagrams to PNG

This guide shows how to convert the Mermaid diagrams to PNG format.

## Option 1: Mermaid Live Editor (Online - Easiest)

1. Visit: https://mermaid.live/
2. Copy a diagram from `ARCHITECTURE_MERMAID.md`
3. Paste into the editor
4. Click "Actions" → "PNG" or "SVG"
5. Download the image

## Option 2: Mermaid CLI (Local - Best Quality)

### Install Mermaid CLI

```powershell
# Install Node.js if not installed (from https://nodejs.org/)
# Then install mermaid-cli
npm install -g @mermaid-js/mermaid-cli
```

### Convert Diagrams

Create individual `.mmd` files for each diagram, then run:

```powershell
# Convert single diagram
mmdc -i system-architecture.mmd -o system-architecture.png

# Convert all diagrams
Get-ChildItem *.mmd | ForEach-Object {
    mmdc -i $_.Name -o ($_.BaseName + ".png")
}

# High quality with custom settings
mmdc -i system-architecture.mmd -o system-architecture.png -w 2048 -H 1536
```

### Extract Diagrams Script

I've created a script to extract all diagrams:

```powershell
# Save as: extract-diagrams.ps1
$content = Get-Content "ARCHITECTURE_MERMAID.md" -Raw
$diagrams = [regex]::Matches($content, '```mermaid\r?\n(.*?)\r?\n```', 'Singleline')

$index = 1
$names = @(
    "system-architecture",
    "langgraph-workflow",
    "node-architecture",
    "data-flow",
    "class-diagram",
    "sequence-diagram",
    "component-interaction",
    "deployment-architecture"
)

foreach ($match in $diagrams) {
    $diagramContent = $match.Groups[1].Value
    $filename = if ($index -le $names.Count) { $names[$index-1] } else { "diagram-$index" }
    Set-Content -Path "$filename.mmd" -Value $diagramContent
    Write-Host "Created: $filename.mmd"
    $index++
}

Write-Host "`nNow run: mmdc -i <filename>.mmd -o <filename>.png"
```

## Option 3: VS Code Extension

1. Install "Markdown Preview Mermaid Support" extension
2. Open `ARCHITECTURE_MERMAID.md`
3. Click "Preview" (Ctrl+Shift+V)
4. Right-click on diagram → "Copy as PNG" or use screenshot tool

## Option 4: GitHub (If Pushed to Repo)

1. Push `ARCHITECTURE_MERMAID.md` to GitHub
2. GitHub automatically renders Mermaid diagrams
3. Use browser screenshot tools to capture

## Option 5: Python Script (Automated)

```python
# Install: pip install playwright pymermaid
# Then run: playwright install chromium

from pymermaid import MermaidRenderer

renderer = MermaidRenderer()

diagrams = {
    "system-architecture": "graph TB...",  # paste diagram code
    "workflow": "stateDiagram-v2..."
}

for name, code in diagrams.items():
    renderer.render_to_file(code, f"{name}.png")
```

## Recommended: Quick PNG Generation

Run this PowerShell script in the project directory:

```powershell
# quick-png.ps1
Write-Host "Opening Mermaid Live Editor..."
Start-Process "https://mermaid.live/"

Write-Host "`nInstructions:"
Write-Host "1. Copy diagrams from ARCHITECTURE_MERMAID.md"
Write-Host "2. Paste into Mermaid Live Editor"
Write-Host "3. Click 'Actions' -> 'PNG'"
Write-Host "4. Save to project diagrams/ folder"
Write-Host "`nDiagrams to convert:"
Write-Host "  - System Architecture"
Write-Host "  - LangGraph Workflow"
Write-Host "  - Node Architecture"
Write-Host "  - Data Flow"
Write-Host "  - Class Diagram"
Write-Host "  - Sequence Diagram"
Write-Host "  - Component Interaction"
Write-Host "  - Deployment Architecture"
```

## Best Quality Settings

When using Mermaid CLI:

```powershell
mmdc -i diagram.mmd -o diagram.png `
  -w 2048 `
  -H 1536 `
  -b white `
  -t default `
  -s 2
```

Parameters:
- `-w`: Width in pixels
- `-H`: Height in pixels
- `-b`: Background color
- `-t`: Theme (default, forest, dark, neutral)
- `-s`: Scale factor

## Batch Conversion Script

Save as `convert-all.ps1`:

```powershell
# Create diagrams directory
New-Item -ItemType Directory -Force -Path "diagrams"

# Extract and convert all diagrams
$content = Get-Content "ARCHITECTURE_MERMAID.md" -Raw
$diagrams = [regex]::Matches($content, '```mermaid\r?\n(.*?)\r?\n```', 'Singleline')

$names = @(
    "system-architecture",
    "langgraph-workflow", 
    "node-architecture",
    "data-flow",
    "class-diagram",
    "sequence-diagram",
    "component-interaction",
    "deployment-architecture"
)

for ($i = 0; $i -lt $diagrams.Count; $i++) {
    $diagramContent = $diagrams[$i].Groups[1].Value
    $name = $names[$i]
    
    # Save .mmd file
    Set-Content -Path "diagrams\$name.mmd" -Value $diagramContent
    
    # Convert to PNG (requires mermaid-cli)
    if (Get-Command mmdc -ErrorAction SilentlyContinue) {
        mmdc -i "diagrams\$name.mmd" -o "diagrams\$name.png" -w 2048 -b white
        Write-Host "✓ Created: diagrams\$name.png"
    }
}

if (-not (Get-Command mmdc -ErrorAction SilentlyContinue)) {
    Write-Host "`nMermaid CLI not found. Install with:"
    Write-Host "  npm install -g @mermaid-js/mermaid-cli"
}
```
