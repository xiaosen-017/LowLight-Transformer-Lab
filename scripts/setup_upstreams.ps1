param([string]$Proxy = '')
$ErrorActionPreference='Stop'
$ProjectRoot=Split-Path -Parent $PSScriptRoot
$Manifest=Get-Content -LiteralPath (Join-Path $ProjectRoot 'configs/upstreams.json') -Raw | ConvertFrom-Json
$GitOptions=@()
if($Proxy){$GitOptions=@('-c',"http.proxy=$Proxy")}
foreach($Entry in $Manifest.PSObject.Properties){
    $Spec=$Entry.Value
    $Target=Join-Path $ProjectRoot $Spec.directory
    $NewClone=$false
    if(!(Test-Path -LiteralPath $Target)){
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Target) | Out-Null
        $NewClone=$true
        & git @GitOptions clone --no-checkout $Spec.url $Target
        if($LASTEXITCODE -ne 0){throw "Official clone failed: $($Spec.url)"}
    }
    $Origin=& git -C $Target remote get-url origin
    if($LASTEXITCODE -ne 0 -or $Origin.Trim() -ne $Spec.url){throw "Unexpected upstream at $Target; refusing to alter it."}
    $Dirty=& git -C $Target status --porcelain --untracked-files=no
    if(!$NewClone -and $Dirty){throw "Tracked modifications at $Target; preserve them before checkout."}
    & git -C $Target cat-file -e "$($Spec.commit)^{commit}" 2>$null
    if($LASTEXITCODE -ne 0){
        & git @GitOptions -C $Target fetch --depth 1 origin $Spec.commit
        if($LASTEXITCODE -ne 0){throw 'Pinned commit fetch failed.'}
    }
    & git -C $Target checkout --detach $Spec.commit
    if($LASTEXITCODE -ne 0){throw 'Pinned checkout failed.'}
    $Actual=& git -C $Target rev-parse HEAD
    if($Actual.Trim() -ne $Spec.commit){throw 'Upstream commit mismatch.'}
    Write-Output "$($Entry.Name): $Actual"
}

