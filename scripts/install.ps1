param(
    [ValidateSet("agents", "claude", "codex", "all")]
    [string]$Target = "all",

    [switch]$Overwrite,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$bundleRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$skillsSource = Join-Path $bundleRoot "skills"
$playbooksSource = Join-Path $bundleRoot "playbooks"

if (-not (Test-Path -LiteralPath $skillsSource)) {
    throw "Missing skills source directory: $skillsSource"
}

if (-not (Test-Path -LiteralPath $playbooksSource)) {
    throw "Missing playbooks source directory: $playbooksSource"
}

function Get-HomePath {
    param([string]$Name)

    if ($env:USERPROFILE) {
        return (Join-Path $env:USERPROFILE $Name)
    }

    return (Join-Path $HOME $Name)
}

function Get-Targets {
    param([string]$Target)

    $knownTargets = @{
        agents = Get-HomePath ".agents"
        claude = Get-HomePath ".claude"
        codex  = Get-HomePath ".codex"
    }

    if ($Target -eq "all") {
        return @(
            @{ Name = "agents"; Root = $knownTargets.agents },
            @{ Name = "claude"; Root = $knownTargets.claude },
            @{ Name = "codex";  Root = $knownTargets.codex }
        )
    }

    return @(@{ Name = $Target; Root = $knownTargets[$Target] })
}

function Copy-DirectoryItem {
    param(
        [string]$Source,
        [string]$Destination,
        [bool]$Overwrite,
        [bool]$DryRun
    )

    if ((Test-Path -LiteralPath $Destination) -and -not $Overwrite -and $DryRun) {
        Write-Host "[dry-run] conflict would block directory $Destination"
        return
    }

    if ((Test-Path -LiteralPath $Destination) -and -not $Overwrite) {
        throw "Conflict: $Destination already exists. Re-run with -Overwrite or install a narrower target."
    }

    if ($DryRun) {
        Write-Host "[dry-run] copy directory $Source -> $Destination"
        return
    }

    if (Test-Path -LiteralPath $Destination) {
        Remove-Item -LiteralPath $Destination -Recurse -Force
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Recurse -Force
}

function Copy-FileItem {
    param(
        [string]$Source,
        [string]$Destination,
        [bool]$Overwrite,
        [bool]$DryRun
    )

    if ((Test-Path -LiteralPath $Destination) -and -not $Overwrite -and $DryRun) {
        Write-Host "[dry-run] conflict would block file $Destination"
        return
    }

    if ((Test-Path -LiteralPath $Destination) -and -not $Overwrite) {
        throw "Conflict: $Destination already exists. Re-run with -Overwrite or merge manually."
    }

    if ($DryRun) {
        Write-Host "[dry-run] copy file $Source -> $Destination"
        return
    }

    Copy-Item -LiteralPath $Source -Destination $Destination -Force
}

$targetInfos = Get-Targets $Target
$conflicts = @()

if (-not $Overwrite -and -not $DryRun) {
    foreach ($targetInfo in $targetInfos) {
        $targetRoot = $targetInfo.Root
        $skillsDest = Join-Path $targetRoot "skills"
        $playbooksDest = Join-Path $targetRoot "playbooks"

        foreach ($skill in Get-ChildItem -LiteralPath $skillsSource -Directory) {
            $dest = Join-Path $skillsDest $skill.Name
            if (Test-Path -LiteralPath $dest) {
                $conflicts += $dest
            }
        }

        foreach ($playbook in Get-ChildItem -LiteralPath $playbooksSource -File) {
            $dest = Join-Path $playbooksDest $playbook.Name
            if (Test-Path -LiteralPath $dest) {
                $conflicts += $dest
            }
        }
    }

    if ($conflicts.Count -gt 0) {
        $message = "Install blocked by existing files. Re-run with -Overwrite or install a narrower target:`n" + ($conflicts | Sort-Object | ForEach-Object { "  $_" } | Out-String)
        throw $message
    }
}

$installed = @()

foreach ($targetInfo in $targetInfos) {
    $targetName = $targetInfo.Name
    $targetRoot = $targetInfo.Root
    $skillsDest = Join-Path $targetRoot "skills"
    $playbooksDest = Join-Path $targetRoot "playbooks"

    if ($DryRun) {
        Write-Host "[dry-run] ensure $skillsDest"
        Write-Host "[dry-run] ensure $playbooksDest"
    }
    else {
        New-Item -ItemType Directory -Force -Path $skillsDest | Out-Null
        New-Item -ItemType Directory -Force -Path $playbooksDest | Out-Null
    }

    foreach ($skill in Get-ChildItem -LiteralPath $skillsSource -Directory) {
        Copy-DirectoryItem `
            -Source $skill.FullName `
            -Destination (Join-Path $skillsDest $skill.Name) `
            -Overwrite $Overwrite `
            -DryRun $DryRun
    }

    foreach ($playbook in Get-ChildItem -LiteralPath $playbooksSource -File) {
        Copy-FileItem `
            -Source $playbook.FullName `
            -Destination (Join-Path $playbooksDest $playbook.Name) `
            -Overwrite $Overwrite `
            -DryRun $DryRun
    }

    $installed += [pscustomobject]@{
        Target = $targetName
        Root = $targetRoot
        Skills = $skillsDest
        Playbooks = $playbooksDest
    }
}

Write-Host ""
Write-Host "Agent Workflow Bundle install summary"
Write-Host "-------------------------------------"
$installed | Format-Table -AutoSize

if (-not $DryRun) {
    Write-Host "Installed skills:"
    Get-ChildItem -LiteralPath $skillsSource -Directory | Select-Object -ExpandProperty Name | Sort-Object | ForEach-Object {
        Write-Host "  /$_"
    }
}
