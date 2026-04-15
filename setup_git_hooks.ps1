#!/usr/bin/env pwsh

$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

git config core.hooksPath .githooks
$hooksPath = git config --get core.hooksPath

if ($hooksPath -eq ".githooks") {
    Write-Host "Git hooks activated: $hooksPath"
    exit 0
}

Write-Error "Failed to activate git hooks. Current core.hooksPath: '$hooksPath'"
exit 1
