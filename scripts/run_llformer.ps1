param([string]$PythonExe='', [string]$Upstream='', [string]$Weights='', [string]$InputPath='', [string]$OutputDir='', [int]$Threads=4)
& (Join-Path $PSScriptRoot 'Run-Model.ps1') -Model 'llformer' -PythonExe $PythonExe -Upstream $Upstream -Weights $Weights -InputPath $InputPath -OutputDir $OutputDir -Threads $Threads
