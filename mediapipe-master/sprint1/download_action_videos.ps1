$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

$Videos = @(
    @{
        Name = "jump_rapidity_test.ogv"
        Url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Analysis-of-Balance-Rapidity-Force-and-Reaction-Times-of-Soccer-Players-at-Different-Levels-of-pone.0077264.s007.ogv"
    },
    @{
        Name = "rugby_side_step_cutting.ogv"
        Url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Detecting-Deception-in-Movement-The-Case-of-the-Side-Step-in-Rugby-pone.0037494.s001.ogv"
    },
    @{
        Name = "soccer_scissors_dribble.ogv"
        Url = "https://commons.wikimedia.org/wiki/Special:Redirect/file/Scissors%20soccer.theora.ogv"
    }
)

New-Item -ItemType Directory -Force -Path "sprint1\input_videos" | Out-Null

foreach ($Video in $Videos) {
    $Output = Join-Path "sprint1\input_videos" $Video.Name
    Write-Host "Downloading $($Video.Name)..."
    Invoke-WebRequest -Uri $Video.Url -OutFile $Output -MaximumRedirection 10
}

Write-Host ""
Write-Host "Downloaded action videos:"
Get-Item sprint1\input_videos\jump_rapidity_test.ogv,
         sprint1\input_videos\rugby_side_step_cutting.ogv,
         sprint1\input_videos\soccer_scissors_dribble.ogv |
    Select-Object FullName, Length, LastWriteTime
