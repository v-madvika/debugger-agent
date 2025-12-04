# Extract Mermaid Diagrams from Markdown
# This script extracts all Mermaid diagrams from ARCHITECTURE_MERMAID.md
# and saves them as individual .mmd files

Write-Host "🎨 Mermaid Diagram Extractor" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if markdown file exists
if (-not (Test-Path "ARCHITECTURE_MERMAID.md")) {
    Write-Host "❌ ARCHITECTURE_MERMAID.md not found!" -ForegroundColor Red
    exit 1
}

# Create diagrams directory
$diagramsDir = "diagrams"
if (-not (Test-Path $diagramsDir)) {
    New-Item -ItemType Directory -Path $diagramsDir | Out-Null
    Write-Host "✓ Created diagrams/ directory" -ForegroundColor Green
}

# Read markdown content
$content = Get-Content "ARCHITECTURE_MERMAID.md" -Raw

# Extract all mermaid code blocks
$pattern = '```mermaid\r?\n(.*?)\r?\n```'
$matches = [regex]::Matches($content, $pattern, [System.Text.RegularExpressions.RegexOptions]::Singleline)

# Diagram names
$names = @(
    "01-system-architecture",
    "02-langgraph-workflow",
    "03-node-architecture",
    "04-data-flow",
    "05-class-diagram",
    "06-sequence-diagram",
    "07-component-interaction",
    "08-deployment-architecture"
)

Write-Host "`nExtracting $($matches.Count) diagrams..." -ForegroundColor Yellow

# Extract each diagram
for ($i = 0; $i -lt $matches.Count; $i++) {
    $diagramContent = $matches[$i].Groups[1].Value.Trim()
    $name = if ($i -lt $names.Count) { $names[$i] } else { "diagram-$($i+1)" }
    $filename = "$diagramsDir\$name.mmd"
    
    Set-Content -Path $filename -Value $diagramContent -Encoding UTF8
    Write-Host "  ✓ $filename" -ForegroundColor Green
}

Write-Host "`n✅ Extracted $($matches.Count) diagrams successfully!" -ForegroundColor Green

# Check if mermaid-cli is installed
Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
if (Get-Command mmdc -ErrorAction SilentlyContinue) {
    Write-Host "  Mermaid CLI is installed! ✓" -ForegroundColor Green
    Write-Host "`n  Convert to PNG:" -ForegroundColor Yellow
    Write-Host "    cd diagrams" -ForegroundColor White
    Write-Host "    mmdc -i 01-system-architecture.mmd -o 01-system-architecture.png -w 2048 -b white" -ForegroundColor White
    Write-Host "`n  Or convert all:" -ForegroundColor Yellow
    Write-Host "    Get-ChildItem diagrams\*.mmd | ForEach-Object { mmdc -i `$_.FullName -o (`$_.FullName -replace '.mmd','.png') -w 2048 -b white }" -ForegroundColor White
} else {
    Write-Host "  ⚠ Mermaid CLI not installed" -ForegroundColor Yellow
    Write-Host "`n  Option 1: Install Mermaid CLI" -ForegroundColor Cyan
    Write-Host "    npm install -g @mermaid-js/mermaid-cli" -ForegroundColor White
    Write-Host "`n  Option 2: Use Online Editor" -ForegroundColor Cyan
    Write-Host "    1. Go to https://mermaid.live/" -ForegroundColor White
    Write-Host "    2. Copy content from .mmd files" -ForegroundColor White
    Write-Host "    3. Click 'PNG' to download" -ForegroundColor White
}

Write-Host "`n📁 Diagram files saved in: $diagramsDir\" -ForegroundColor Cyan
