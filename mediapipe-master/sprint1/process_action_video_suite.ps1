$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$VideoJobs = @(
    @{
        Name = "special_olympics_running"
        Video = "sprint1\input_videos\special_olympics_running.webm"
    },
    @{
        Name = "jump_rapidity_test"
        Video = "sprint1\input_videos\jump_rapidity_test.ogv"
    },
    @{
        Name = "rugby_side_step_cutting"
        Video = "sprint1\input_videos\rugby_side_step_cutting.ogv"
    },
    @{
        Name = "soccer_scissors_dribble"
        Video = "sprint1\input_videos\soccer_scissors_dribble.ogv"
    }
)

foreach ($Job in $VideoJobs) {
    if (-not (Test-Path $Job.Video)) {
        Write-Host "Skipping missing video: $($Job.Video)"
        continue
    }

    $Csv = "sprint1\outputs\$($Job.Name)_enhanced.csv"
    $Overlay = "sprint1\outputs\$($Job.Name)_enhanced_overlay.mp4"
    $Summary = "sprint1\outputs\$($Job.Name)_enhanced_summary.md"

    Write-Host "Processing $($Job.Video)..."
    & $Python sprint1\pose_pipeline.py $Job.Video --output $Csv --overlay-output $Overlay --summary-output $Summary
}

Write-Host ""
Write-Host "Sprint 1 action video processing complete."
Get-ChildItem sprint1\outputs\*_enhanced_summary.md | Select-Object FullName, Length, LastWriteTime
