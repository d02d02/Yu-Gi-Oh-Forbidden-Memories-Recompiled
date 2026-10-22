# Play / screenshot a test duel with the Test scenes, 3D Monsters and Forbidden Memories HD (assets-hd; -NoHd drops it) mods ONLY:
# nothing else enabled (no Duel Links art, no Kuriboh, no other data mods),
# its own profile (shared\test-user-bls), a private copy of the build (your build folder is never locked).
#
#   .\play-bls.ps1                                  # Black Luster Soldier (364) on your first zone, five Kuriboh (58) opposite, attack on the field, 2x
#   .\play-bls.ps1 -Cards '364,0,0,0,0,374,0,0,0,0' -Scale 2
#   .\play-bls.ps1 -Mods dragon_mod -Cards '400,0,0,0,0,722,0,0,0,0'   # a mod's native models (by mod id) instead of -NativeModel
#   .\play-bls.ps1 -Attack 0                        # no attack presentation (monsters just stand on the field)
#   .\play-bls.ps1 -Shot C:\temp\bls.ppm            # no play: reach the scene, dump one picture, exit by itself (max -TimeoutS seconds)
#   .\play-bls.ps1 -Repo ..\..\..\Yu-Gi-Oh-Forbidden-Memories-Recompiled-hd-model-bls   # another build (needs the test-scenes mod linked in it)
#
# Why not play-test.ps1: that one copies your real settings (Duel Links 2D Arts, Forbidden Memories HD, ... all on) and links your data mods,
# which made the start stall for minutes in the field-art quantiser. This one starts a vanilla profile.
param(
    [string]$Cards = '364,0,0,0,0,58,58,58,58,58',
    [int]$Scale = 2,
    [ValidateSet(0, 1, 2, 3)][int]$Attack = 2,
    [string]$Shot = '',
    [int]$ShotFrame = 2400,
    [switch]$NoHd,
    [string[]]$Mods = @(),       # more mods to switch on, by mod id (a native_models mod from the build's mods folder: dragon_mod, native-test, ...)
    [string]$Log = '',           # save the game's messages (stderr) to this file
    [string]$NativeModel = '',   # a model.hdm or a package's model.json: drawn for model -NativeId (-2: every monster), over every mod's
    [int]$NativeId = 363,        # model id = card id - 1 (BLS: card 364, model 363)
    [int]$TimeoutS = 150,
    [string]$Repo = "$PSScriptRoot\..\..\..\Yu-Gi-Oh-Forbidden-Memories-Recompiled-dev"
)
$ErrorActionPreference = 'Stop'
$shared = (Resolve-Path "$PSScriptRoot\..\..").Path
$repo = (Resolve-Path $Repo).Path
$build = "$repo\tmp\pc\game32"
if (-not (Test-Path "$build\memories-pc.exe")) { throw "no build in $build" }

# a private copy of the build (robocopy only copies what changed)
$priv = "$shared\tools\hd-models\_exe"
robocopy $build $priv /MIR /NFL /NDL /NJH /NJS /NP /XD mods | Out-Null
foreach ($m in 'test-scenes', '3d-monsters') {
    if (-not (Test-Path "$build\mods\$m")) { throw "the build has no mod '$m' (use the -dev build, or link it: shared\link.ps1)" }
}
robocopy "$build\mods" "$priv\mods" /MIR /NFL /NDL /NJH /NJS /NP | Out-Null

# a vanilla profile: every other mod the build carries is off
$user = "$shared\test-user-bls"
New-Item -ItemType Directory -Force -Path $user | Out-Null
$off = Get-ChildItem "$build\mods" -Directory | ForEach-Object { $_.Name } |
    Where-Object { $_ -notin 'test-scenes', '3d-monsters' } | Where-Object { $_ -notin $Mods }
$lines = @("internal_scale=$Scale", 'show_hud=0', 'fullscreen=0', 'mod.test-scenes=1', 'mod.3d-monsters=1', "mod.3d-monsters.attack=$Attack")
$lines += $off | ForEach-Object { "mod.$_=0" }
$lines += $Mods | ForEach-Object { "mod.$_=1" }
$lines += 'mod.duel-links-2d-arts=0', 'mod.2d-monsters=0', 'mod.camera-pin=0', 'mod.kuriboh=0', 'mod.kuriboh-hd=0'
# The Forbidden Memories HD pack: only assets-hd is linked (your single copy in shared\mods-data), with the settings of your real profile.
$lines += "mod.forbidden-memories-hd=$(if ($NoHd) { 0 } else { 1 })"
if (-not $NoHd) {
    $lines += Get-Content "$shared\user\settings.txt" | Where-Object { $_ -like 'mod.forbidden-memories-hd.*' }
    New-Item -ItemType Directory -Force -Path "$user\mods" | Out-Null
    if (-not (Test-Path "$user\mods\assets-hd")) {
        New-Item -ItemType Junction -Path "$user\mods\assets-hd" -Target "$shared\mods-data\assets-hd" | Out-Null
    }
}
Set-Content -Path "$user\settings.txt" -Value $lines -Encoding ASCII

$env:MEMORIES_USER_DIR = $user
$env:MEMORIES_INTERNAL_SCALE = "$Scale"
$env:MEMORIES_CHECK_FOR_UPDATES = '0'
$env:MEMORIES_MOD_TEST_SCENES = '1'
$ids = $Cards -split ',' | ForEach-Object { $_.Trim() }
if ($ids.Count -ne 10) { throw "-Cards needs ten ids: five yours, five the opponent's" }
for ($i = 0; $i -lt 5; $i++) {
    Set-Item "env:MEMORIES_MOD_TEST_SCENES_P$($i + 1)" $ids[$i]
    Set-Item "env:MEMORIES_MOD_TEST_SCENES_O$($i + 1)" $ids[$i + 5]
}
# the title: down to Option, L1 held, confirm (as scene_measure.py does)
$env:MEMORIES_INPUT = '910:0008,916:0000,1000:0040,1006:0000,1020:0040,1026:0000,1040:0040,1046:0000,1060:0040,1066:0000,1100:4400,1106:0000'
if ($NativeModel) {
    $env:MEMORIES_NATIVE_MODEL = (Resolve-Path $NativeModel).Path
    $env:MEMORIES_NATIVE_MODEL_ID = "$NativeId"
    $env:MEMORIES_NATIVE_MODEL_LOG = '1'
} else {
    Remove-Item env:MEMORIES_NATIVE_MODEL, env:MEMORIES_NATIVE_MODEL_ID, env:MEMORIES_NATIVE_MODEL_LOG -ErrorAction SilentlyContinue
}
if ($Shot) {
    $env:MEMORIES_DUMP_FRAME = "$ShotFrame"
    $env:MEMORIES_DUMP_PICTURE = '1'
    $env:MEMORIES_DUMP_PATH = $Shot
    $env:MEMORIES_DETERMINISTIC = '1'   # a real window and GL, but frame-exact: two shots at one frame are comparable pixel by pixel
    Remove-Item $Shot -ErrorAction SilentlyContinue
}
Write-Host "BLS test: mods = test-scenes + 3d-monsters + HD pack (unless -NoHd), scale ${Scale}x, attack mode $Attack, cards $Cards"
$startArgs = @{ FilePath = "$priv\memories-pc.exe"; WorkingDirectory = $repo; PassThru = $true }
if ($Log) { $startArgs.RedirectStandardError = $Log; $startArgs.RedirectStandardOutput = "$Log.out" }
$p = Start-Process @startArgs
$sw = [Diagnostics.Stopwatch]::StartNew()
if ($Shot) {
    while (-not $p.HasExited -and $sw.Elapsed.TotalSeconds -lt $TimeoutS) { Start-Sleep -Milliseconds 500 }
    if (-not $p.HasExited) { Stop-Process -Id $p.Id -Force; Write-Warning "no picture after $TimeoutS s: stopped our own process" }
    Write-Host ("picture: {0} ({1})" -f $Shot, $(if (Test-Path $Shot) { 'written' } else { 'MISSING' }))
} else {
    $p.WaitForExit()
    Write-Host "game exited with code $($p.ExitCode)"
}

# The variables this script set stay in the PowerShell session otherwise, and a later run from it (even a .bat) inherits them
# (a dump frame makes the game quit): take them away again.
Remove-Item Env:MEMORIES_DUMP_FRAME, Env:MEMORIES_DUMP_PICTURE, Env:MEMORIES_DUMP_PATH, Env:MEMORIES_DETERMINISTIC, Env:MEMORIES_NATIVE_MODEL, Env:MEMORIES_NATIVE_MODEL_ID, Env:MEMORIES_NATIVE_MODEL_LOG, Env:MEMORIES_INPUT -ErrorAction SilentlyContinue
