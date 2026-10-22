param(
    [Parameter(Mandatory = $true)]
    [string]$Target,
    [string]$Agent = "generic",
    [switch]$Update,
    [switch]$DryRun
)

$InstallArgs = @(
    "$PSScriptRoot\scripts\install_agent_skill.py",
    "--target", $Target,
    "--agent", $Agent
)
if ($Update) { $InstallArgs += "--update" }
if ($DryRun) { $InstallArgs += "--dry-run" }

python @InstallArgs
exit $LASTEXITCODE
