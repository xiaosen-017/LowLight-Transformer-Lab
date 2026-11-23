param(
 [string]$RetPython='.venvs/retinexformer/Scripts/python.exe',
 [string]$LLPython='.venvs/llformer/Scripts/python.exe',
 [string]$RetUpstream='third_party/Retinexformer',
 [string]$LLUpstream='third_party/LLFormer',
 [string]$RetWeights='weights/retinexformer/LOL_v1.pth',
 [string]$LLWeights='weights/llformer/model_bestPSNR.pth',
 [string]$OutputDir=''
)
$ErrorActionPreference='Stop'
$ProjectRoot=Split-Path -Parent $PSScriptRoot
function Absolute([string]$Value){if([IO.Path]::IsPathRooted($Value)){return $Value};return Join-Path $ProjectRoot $Value}
if(!$OutputDir){$OutputDir='runs/m2/'+(Get-Date -Format yyyyMMdd_HHmmss)}
$Interpreter=Absolute $RetPython
$OldEncoding=$env:PYTHONIOENCODING
try {
 $env:PYTHONIOENCODING='utf-8'
 & $Interpreter -u (Join-Path $PSScriptRoot 'run_m2.py') --ret-python (Absolute $RetPython) --ll-python (Absolute $LLPython) --ret-repo (Absolute $RetUpstream) --ll-repo (Absolute $LLUpstream) --ret-weights (Absolute $RetWeights) --ll-weights (Absolute $LLWeights) --output (Absolute $OutputDir)
 if($LASTEXITCODE -ne 0){throw 'M2 failed; keep the run logs and inspect the error.'}
} finally {$env:PYTHONIOENCODING=$OldEncoding}
