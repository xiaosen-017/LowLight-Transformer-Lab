param(
 [Parameter(Mandatory=$true)][ValidateSet('retinexformer','llformer')][string]$Model,
 [string]$PythonExe='', [string]$Upstream='', [string]$Weights='',
 [string]$InputPath='', [string]$OutputDir='', [int]$Threads=4
)
$ErrorActionPreference='Stop'
$ProjectRoot=Split-Path -Parent $PSScriptRoot
function Absolute([string]$Value){if([IO.Path]::IsPathRooted($Value)){return $Value}; return Join-Path $ProjectRoot $Value}
$UpstreamName=if($Model -eq 'retinexformer'){'Retinexformer'}else{'LLFormer'}
$Upstreams=Get-Content (Join-Path $ProjectRoot 'configs/upstreams.json') -Raw | ConvertFrom-Json
$WeightSpecs=Get-Content (Join-Path $ProjectRoot 'configs/weights.json') -Raw | ConvertFrom-Json
$WeightSpec=$WeightSpecs | Where-Object {$_.model.ToLower() -eq $Model}
if(!$PythonExe){$PythonExe=".venvs/$Model/Scripts/python.exe"}
if(!$Upstream){$Upstream=$Upstreams.$UpstreamName.directory}
if(!$Weights){$Weights=$WeightSpec.path}
if(!$InputPath){$InputPath='third_party/Retinexformer/demo/examples/111.png'}
if(!$OutputDir){$OutputDir="runs/$Model/"+(Get-Date -Format yyyyMMdd_HHmmss)}
$PythonExe=Absolute $PythonExe; $Upstream=Absolute $Upstream; $Weights=Absolute $Weights; $InputPath=Absolute $InputPath; $OutputDir=Absolute $OutputDir
if(!(Test-Path $PythonExe)){throw "Python missing. Use -PythonExe <your isolated environment interpreter>; see docs/run_$Model.md"}
if(!(Test-Path $Weights)){throw "Official weight missing: $($WeightSpec.name). See weights/README.md. Download from $($WeightSpec.official_source)"}
if((Get-Item $Weights).Length -ne $WeightSpec.size -or (Get-FileHash $Weights -Algorithm SHA256).Hash.ToLower() -ne $WeightSpec.sha256){throw 'Official weight size/hash mismatch; refusing inference.'}
if(!(Test-Path $Upstream)){throw 'Official upstream missing. Run scripts/setup_upstreams.ps1 or provide -Upstream.'}
$Commit=& git -C $Upstream rev-parse HEAD
if($LASTEXITCODE -ne 0 -or $Commit.Trim() -ne $Upstreams.$UpstreamName.commit){throw 'Upstream does not match the M1 pinned commit.'}
$Dirty=& git -C $Upstream diff --name-only
if($Dirty){throw 'Upstream has tracked changes; M1 entry requires original pinned source.'}
if(!(Test-Path -LiteralPath $InputPath -PathType Leaf)){throw 'One real input image is required. See data/README.md; use -InputPath.'}
if($Threads -lt 1){throw 'Threads must be positive.'}
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$Images=Join-Path $OutputDir 'images'; New-Item -ItemType Directory -Force $Images | Out-Null
$Log=Join-Path $OutputDir 'inference.log'
$OldPythonPath=$env:PYTHONPATH; $OldUserSite=$env:PYTHONNOUSERSITE; $OldBytecode=$env:PYTHONDONTWRITEBYTECODE; $OldEncoding=$env:PYTHONIOENCODING
try {
 $env:PYTHONPATH=$Upstream; $env:PYTHONNOUSERSITE='1'; $env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONIOENCODING='utf-8'
 if($Model -eq 'retinexformer'){
  $Arguments=@('-u',(Join-Path $PSScriptRoot 'infer_retinexformer.py'),'--repo',$Upstream,'--weights',$Weights,'--input',$InputPath,'--output',(Join-Path $Images (([IO.Path]::GetFileNameWithoutExtension($InputPath))+'.png')),'--threads',"$Threads")
 } else {
  $StagedInput=Join-Path $OutputDir 'input'; New-Item -ItemType Directory -Force $StagedInput | Out-Null
  $SingleImage=Join-Path $StagedInput ([IO.Path]::GetFileName($InputPath)); Copy-Item -LiteralPath $InputPath -Destination $SingleImage
  $Arguments=@('-u',(Join-Path $ProjectRoot 'patches/test_llformer_cpu.py'),'--input_dir',$StagedInput,'--result_dir',$Images,'--weights',$Weights,'--device','cpu','--threads',"$Threads")
 }
 Write-Output "M1 single-image local CPU inference; output: $Images"
 $ErrorActionPreference='Continue'
 & $PythonExe @Arguments 2>&1 | Tee-Object -FilePath $Log
 $ModelExit=$LASTEXITCODE
 $ErrorActionPreference='Stop'
 if($ModelExit -ne 0){throw "Inference failed (exit $ModelExit). See $Log"}
 Write-Output "SUCCESS. Runtime output saved under $OutputDir (historical results/m1 unchanged)."
} finally {
 $env:PYTHONPATH=$OldPythonPath; $env:PYTHONNOUSERSITE=$OldUserSite; $env:PYTHONDONTWRITEBYTECODE=$OldBytecode; $env:PYTHONIOENCODING=$OldEncoding
}
