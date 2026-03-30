param(
    [string]$Repo = "iznaagc/pyxel-tutorial"
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "== $Title =="
}

function Write-Result {
    param(
        [string]$Label,
        [bool]$Ok,
        [string]$Detail
    )

    $status = if ($Ok) { "OK" } else { "NG" }
    Write-Host ("[{0}] {1}: {2}" -f $status, $Label, $Detail)
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$mcpPath = Join-Path $repoRoot ".mcp.json"

Write-Host "GitHub task environment diagnostics"
Write-Host "Repository root: $repoRoot"
Write-Host "Target repo: $Repo"

Write-Section "Project MCP Config"
$hasMcpFile = Test-Path -LiteralPath $mcpPath
Write-Result ".mcp.json" $hasMcpFile ($(if ($hasMcpFile) { $mcpPath } else { "not found" }))

$hasGithubMcp = $false
if ($hasMcpFile) {
    try {
        $mcpConfig = Get-Content -LiteralPath $mcpPath -Raw | ConvertFrom-Json
        $hasGithubMcp = $null -ne $mcpConfig.mcpServers.github
    } catch {
        $hasGithubMcp = $false
    }
}
Write-Result "github MCP entry" $hasGithubMcp ($(if ($hasGithubMcp) { "configured in .mcp.json" } else { "missing or unreadable" }))

Write-Section "Environment"
$hasGithubPat = -not [string]::IsNullOrWhiteSpace($env:GITHUB_PAT)
Write-Result "GITHUB_PAT" $hasGithubPat ($(if ($hasGithubPat) { "set" } else { "not set" }))

$ghCommand = Get-Command gh -ErrorAction SilentlyContinue
$hasGh = $null -ne $ghCommand
Write-Result "gh CLI" $hasGh ($(if ($hasGh) { $ghCommand.Source } else { "gh command not found" }))

$npxCommand = Get-Command npx -ErrorAction SilentlyContinue
$hasNpx = $null -ne $npxCommand
Write-Result "npx" $hasNpx ($(if ($hasNpx) { $npxCommand.Source } else { "npx command not found" }))

Write-Section "GitHub Auth"
$ghAuthOk = $false
if ($hasGh) {
    $ghAuthOutput = & gh auth status 2>&1
    $ghAuthText = ($ghAuthOutput | Out-String).Trim()
    $ghAuthOk = $LASTEXITCODE -eq 0 -and $ghAuthText -notmatch "invalid"
    Write-Result "gh auth status" $ghAuthOk $ghAuthText
} else {
    Write-Result "gh auth status" $false "gh is not installed"
}

$issueAccessOk = $false
if ($hasGh -and $ghAuthOk) {
    $issueOutput = & gh issue list --repo $Repo --state open --limit 1 2>&1
    $issueText = ($issueOutput | Out-String).Trim()
    $issueAccessOk = $LASTEXITCODE -eq 0
    Write-Result "gh issue list" $issueAccessOk ($(if ($issueAccessOk) { "repository access succeeded" } else { $issueText }))
} else {
    Write-Result "gh issue list" $false "skipped because gh auth is not ready"
}

Write-Section "Next Actions"
$actions = [System.Collections.Generic.List[string]]::new()

if (-not $hasGithubPat) {
    $actions.Add("Set the user environment variable GITHUB_PAT to a valid fine-grained PAT for $Repo.")
}
if (-not $ghAuthOk) {
    $actions.Add("Run 'gh auth login -h github.com' and complete browser authentication.")
}
if ($hasGithubPat -or $ghAuthOk) {
    $actions.Add("Restart Codex after auth changes so the session reloads MCP and connector state.")
}
if (-not $issueAccessOk -and $ghAuthOk) {
    $actions.Add("Verify the token has Issues/PR read-write and repository scope for $Repo.")
}
if ($actions.Count -eq 0) {
    $actions.Add("Environment looks ready. You can start issue-based work from Codex.")
}

for ($i = 0; $i -lt $actions.Count; $i++) {
    Write-Host ("{0}. {1}" -f ($i + 1), $actions[$i])
}
