<#
.SYNOPSIS
    One-click installer for x-use on Windows.

.DESCRIPTION
    1. Preflight: git and Python >= 3.10 must be present.
    2. Clone the repo (or reuse/update an existing clone, or install in
       place when run from inside the repo).
    3. Create a virtual environment (venv\) and install x-use into it.
    4. Bootstrap local config: .env and config\accounts.json from the
       shipped examples (never overwrites existing files).
    5. Run `x-use doctor` so you immediately see what is left to set up.

    The script is idempotent: re-running it reuses the clone and the venv.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File install.ps1

.EXAMPLE
    iex "& { $(irm https://raw.githubusercontent.com/ihuzaifashoukat/x-use/main/install.ps1) }"

.EXAMPLE
    .\install.ps1 -Dir C:\tools\x-use -Dev -Update
#>
[CmdletBinding()]
param(
    # Install directory. Defaults to .\x-use, or the current directory when
    # run from inside the repo. Env: XUSE_INSTALL_DIR (used by irm|iex).
    [string]$Dir = $(if ($env:XUSE_INSTALL_DIR) { $env:XUSE_INSTALL_DIR } else { "" }),
    # Install with dev extras (pytest) for contributors.
    [switch]$Dev,
    # git pull --ff-only an existing checkout before installing.
    [switch]$Update,
    # Show usage and exit.
    [switch]$Help
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoUrl = if ($env:XUSE_REPO_URL) { $env:XUSE_REPO_URL } else { "https://github.com/ihuzaifashoukat/x-use.git" }
$MinPythonMajor = 3
$MinPythonMinor = 10

function Write-Info([string]$Msg) { Write-Host "==> $Msg" -ForegroundColor Green }
function Write-Warn([string]$Msg) { Write-Host "warn: $Msg" -ForegroundColor Yellow }
function Fail([string]$Msg) { Write-Host "error: $Msg" -ForegroundColor Red; exit 1 }

# Native commands do not throw on failure; check the exit code ourselves.
function Invoke-Native([string]$File, [string[]]$CmdArgs, [string]$What) {
    & $File @CmdArgs
    if ($LASTEXITCODE -ne 0) { Fail "$What failed (exit code $LASTEXITCODE)." }
}

if ($Help) {
    Get-Help $MyInvocation.MyCommand.Path
    exit 0
}

# --- preflight ------------------------------------------------------------------

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Fail "git is not installed (or not on PATH). Get it from https://git-scm.com/download/win"
}

$Python = $null
$candidates = @()
if (Get-Command py -ErrorAction SilentlyContinue) { $candidates += , @("py", @("-3")) }
if (Get-Command python -ErrorAction SilentlyContinue) { $candidates += , @("python", @()) }
foreach ($candidate in $candidates) {
    $exe = $candidate[0]; $exeArgs = $candidate[1]
    & $exe @exeArgs -c "import sys; raise SystemExit(0 if sys.version_info >= ($MinPythonMajor, $MinPythonMinor) else 1)" 2>$null
    if ($LASTEXITCODE -eq 0) { $Python = $candidate; break }
}
if (-not $Python) {
    Fail "Python $MinPythonMajor.$MinPythonMinor+ not found. Install it from https://www.python.org/downloads/ (tick 'Add python.exe to PATH') and re-run."
}
$pyExe = $Python[0]; $pyArgs = $Python[1]
# No embedded double quotes in -c strings: PowerShell strips them when
# passing arguments to native commands.
$pyVersion = (& $pyExe @pyArgs -c 'import sys; print(sys.version.split()[0])')
$gitVersion = (git --version) -replace '^git version ', ''
Write-Info "git $gitVersion, python $pyVersion - preflight OK."

# --- repo: clone / update / in-place ---------------------------------------------

function Test-XUseCheckout([string]$Path) {
    $pyproject = Join-Path $Path "pyproject.toml"
    if (-not (Test-Path $pyproject)) { return $false }
    return [bool](Select-String -Path $pyproject -Pattern '^name = "x-use' -Quiet)
}

if (-not $Dir -and (Test-XUseCheckout (Get-Location).Path)) {
    # Running from inside the repo: install in place.
    $Dir = (Get-Location).Path
}
if (-not $Dir) { $Dir = "x-use" }

if (Test-XUseCheckout $Dir) {
    if ($Update) {
        Write-Info "Updating existing clone in $Dir ..."
        git -C $Dir pull --ff-only
        if ($LASTEXITCODE -ne 0) { Write-Warn "git pull failed - keeping the existing checkout." }
    } else {
        Write-Info "Existing x-use checkout found in $Dir - reusing it (pass -Update to pull latest)."
    }
} else {
    if (Test-Path $Dir) {
        Fail "'$Dir' exists but is not an x-use checkout. Pick another -Dir or remove it."
    }
    Write-Info "Cloning $RepoUrl -> $Dir ..."
    Invoke-Native git @("clone", "--depth", "1", $RepoUrl, $Dir) "git clone"
    if (-not (Test-XUseCheckout $Dir)) {
        Fail "the clone does not look like x-use v2 (missing pyproject.toml). The default branch may predate the v2 merge - clone the right branch or set XUSE_REPO_URL."
    }
}
$Dir = (Resolve-Path $Dir).Path

# --- virtual environment -----------------------------------------------------------

$venvDir = Join-Path $Dir "venv"
if (Test-Path $venvDir) {
    Write-Info "Virtual environment already exists at $venvDir - reusing it."
} else {
    Write-Info "Creating virtual environment at $venvDir ..."
    Invoke-Native $pyExe ($pyArgs + @("-m", "venv", $venvDir)) "python -m venv"
}
$venvPy = Join-Path $venvDir "Scripts\python.exe"
if (-not (Test-Path $venvPy)) { Fail "venv created at $venvDir but Scripts\python.exe was not found." }
$binDir = Split-Path $venvPy

# --- install ------------------------------------------------------------------------

Write-Info "Installing x-use (this can take a minute) ..."
Invoke-Native $venvPy @("-m", "pip", "install", "--quiet", "--upgrade", "pip") "pip upgrade"
Push-Location $Dir
try {
    if ($Dev) {
        Invoke-Native $venvPy @("-m", "pip", "install", "--quiet", "-e", ".[dev]") "pip install"
    } else {
        Invoke-Native $venvPy @("-m", "pip", "install", "--quiet", "-e", ".") "pip install"
    }
} finally {
    Pop-Location
}

$xuseBin = Join-Path $binDir "x-use.exe"
if (-not (Test-Path $xuseBin)) { Fail "install finished but x-use.exe was not found in $binDir." }
& $xuseBin --help | Out-Null
if ($LASTEXITCODE -ne 0) { Fail "x-use was installed but fails to run ($xuseBin --help)." }
Write-Info "Installed x-use -> $xuseBin"

# --- config bootstrap (never overwrites) ----------------------------------------------

$envExample = Join-Path $Dir ".env.example"
$envFile = Join-Path $Dir ".env"
if ((Test-Path $envExample) -and -not (Test-Path $envFile)) {
    Copy-Item $envExample $envFile
    Write-Info "Created .env from .env.example - add your LLM API key(s) there."
}
$accountsExample = Join-Path $Dir "config\accounts.example.json"
$accountsFile = Join-Path $Dir "config\accounts.json"
if ((Test-Path $accountsExample) -and -not (Test-Path $accountsFile)) {
    Copy-Item $accountsExample $accountsFile
    Write-Info "Created config\accounts.json from the example (ships inactive - configure it via x-use init)."
}

# --- doctor ----------------------------------------------------------------------------

Write-Info "Running preflight checks (x-use doctor) ..."
Push-Location $Dir
try {
    & $xuseBin doctor
    $doctorFailed = ($LASTEXITCODE -ne 0)
} finally {
    Pop-Location
}

# --- done -------------------------------------------------------------------------------

Write-Host ""
Write-Host "x-use is installed." -ForegroundColor White
if ($doctorFailed) {
    Write-Warn "doctor reported issues above - fix the FAIL rows, then you are set."
}
Write-Host @"

Next steps:
  1. cd $Dir
  2. $xuseBin init      # interactive wizard: account, cookies, LLM keys
  3. $xuseBin doctor    # re-check until every row is PASS/SKIP
  4. $xuseBin run       # or connect an MCP client (below)

MCP client config (claude_desktop_config.json):
  {
    "mcpServers": {
      "x-use": {
        "command": "$($xuseBin -replace '\\', '\\')",
        "args": ["mcp"]
      }
    }
  }

Docs: README.md, BEST_PRACTICES.md, docs\CONFIG_REFERENCE.md
"@

# Exit 0 explicitly: doctor's non-zero exit (unconfigured setup is expected on
# first install) must not make a successful install look failed to callers.
exit 0
