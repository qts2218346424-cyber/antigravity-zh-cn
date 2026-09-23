<#
.SYNOPSIS
    Antigravity Windows 后台自动维护看门狗脚本 (watchdog.ps1)
.DESCRIPTION
    静默运行在后台，监测 Antigravity 程序的更新状态与汉化完整度。
    若发现官方更新覆盖了 app.asar，自动拉取新词条、增量翻译、执行单测、重打补丁并推送到 GitHub。
#>

$ErrorActionPreference = "SilentlyContinue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Split-Path -Parent $ScriptDir
$LogFile = Join-Path $ScriptDir "watchdog.log"

function Write-WatchdogLog {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $Line = "[$Timestamp] $Message"
    Add-Content -Path $LogFile -Value $Line -Encoding UTF8
    Write-Output $Line
}

Write-WatchdogLog "=== 启动 Antigravity 看门狗检测 ==="

# 检测 Python 环境
$PythonExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PythonExe) {
    Write-WatchdogLog "❌ 未找到系统 Python 命令，检测中止。"
    exit 1
}

# 执行自动化维护脚本
$MaintainerScript = Join-Path $ScriptDir "auto_maintainer.py"
if (-not (Test-Path $MaintainerScript)) {
    Write-WatchdogLog "❌ 未找到 auto_maintainer.py 脚本文件。"
    exit 1
}

Write-WatchdogLog "正在执行 auto_maintainer.py 自动化维护流水线..."
$ProcessInfo = New-Object System.Diagnostics.ProcessStartInfo
$ProcessInfo.FileName = $PythonExe
$ProcessInfo.Arguments = "`"$MaintainerScript`""
$ProcessInfo.WorkingDirectory = $RepoRoot
$ProcessInfo.RedirectStandardOutput = $true
$ProcessInfo.RedirectStandardError = $true
$ProcessInfo.UseShellExecute = $false
$ProcessInfo.CreateNoWindow = $true

$Process = New-Object System.Diagnostics.Process
$Process.StartInfo = $ProcessInfo
$Process.Start() | Out-Null
$Stdout = $Process.StandardOutput.ReadToEnd()
$Stderr = $Process.StandardError.ReadToEnd()
$Process.WaitForExit()

if ($Process.ExitCode -eq 0) {
    Write-WatchdogLog "✅ 维护流程执行成功！"
    if ($Stdout) {
        $Stdout.Split("`n") | ForEach-Object {
            if ($_.Trim()) { Write-WatchdogLog "  > $($_.Trim())" }
        }
    }
} else {
    Write-WatchdogLog "⚠ 维护流程退出码: $($Process.ExitCode)"
    if ($Stderr) { Write-WatchdogLog "  错误信息: $Stderr" }
}

Write-WatchdogLog "=== 看门狗检测结束 ==="
