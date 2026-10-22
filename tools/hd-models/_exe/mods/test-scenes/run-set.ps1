# Start a game install with one of sets\<name>.json as the test-scenes duel (test-scenes 1.1).
# A set is {"player": [5 ids], "opponent": [5 ids]} (0 = empty zone; "hand" keys are ignored).
# Usage: .\run-set.ps1 -Install C:\path\to\game -Set mixed [-User C:\path\to\user-dir]
# Then hold L1 and confirm Option on the title screen.
param([Parameter(Mandatory)][string]$Install, [Parameter(Mandatory)][string]$Set, [string]$User)
$file = Join-Path $PSScriptRoot "sets\$Set.json"
if (-not (Test-Path $file)) { throw "no set $Set (see sets\)" }
$scene = Get-Content $file -Raw | ConvertFrom-Json
for ($i = 0; $i -lt 5; $i++) {
    Set-Item "env:MEMORIES_MOD_TEST_SCENES_P$($i + 1)" $scene.player[$i]
    Set-Item "env:MEMORIES_MOD_TEST_SCENES_O$($i + 1)" $scene.opponent[$i]
}
if ($User) { $env:MEMORIES_USER_DIR = $User }
Set-Location $Install
& .\memories-pc.exe
