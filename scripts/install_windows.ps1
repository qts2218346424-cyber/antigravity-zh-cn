<#
.SYNOPSIS
    Antigravity Windows 简体中文汉化补丁安装/管理脚本
.DESCRIPTION
    Antigravity 交互式汉化与管理工具。
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("interactive", "install", "restore", "disable-updates", "enable-updates")]
    [string]$Action = "interactive",

    [Parameter(Position = 1)]
    [ValidateSet("zh-CN", "zh-TW", "zh-HK")]
    [string]$Language = "zh-CN",

    [string]$CustomInstallDir = ""
)

$ErrorActionPreference = "Stop"

# 兼容各种 Windows 控制台环境的编码配置
try { [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}
try { [Console]::InputEncoding = [System.Text.UTF8Encoding]::new() } catch {}
try { $OutputEncoding = [System.Text.UTF8Encoding]::new() } catch {}
try { chcp 65001 >$null } catch {}

try {
    $Host.UI.RawUI.WindowTitle = "Antigravity 简体中文汉化补丁管理器"
} catch {}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PatcherPy = Join-Path $ScriptDir "patch_antigravity.py"

function Write-Color([string]$text, [ConsoleColor]$color = [ConsoleColor]::White) {
    Write-Host $text -ForegroundColor $color
}

function Show-Header {
    try { Clear-Host } catch {}
    Write-Color "============================================================" Cyan
    Write-Color "         Antigravity 简体中文汉化补丁管理器                 " Cyan
    Write-Color "============================================================" Cyan
    Write-Host ""
}

function Find-AntigravityDirectory {
    if ($CustomInstallDir -and (Test-Path -LiteralPath (Join-Path $CustomInstallDir "resources\app.asar"))) {
        return $CustomInstallDir
    }

    $candidates = @(
        (Join-Path $env:LOCALAPPDATA "Programs\antigravity"),
        (Join-Path $env:ProgramFiles "antigravity"),
        (Join-Path ${env:ProgramFiles(x86)} "antigravity")
    )

    foreach ($dir in $candidates) {
        if ($dir -and (Test-Path -LiteralPath (Join-Path $dir "resources\app.asar"))) {
            return $dir
        }
    }

    return $null
}

function Stop-AntigravityProcesses {
    $processes = Get-Process -Name "Antigravity", "language_server" -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Color "检测到 Antigravity 或后台语言服务正在运行，正在安全关闭..." Yellow
        $processes | Stop-Process -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
        Write-Color "[OK] 进程已关闭。" Green
    }
}

function Check-PythonEnvironment {
    try {
        $ver = & python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            return $true
        }
    } catch {}

    Write-Color "[!] 错误: 未检测到系统 Python 3 环境！" Red
    Write-Color "请先安装 Python 3 (https://www.python.org/downloads/) 并勾选 Add Python to PATH。" Yellow
    return $false
}

function Invoke-PatchAction([string]$op, [string]$lang = "zh-CN", [string]$dir = "") {
    if (-not (Check-PythonEnvironment)) {
        return $false
    }

    Stop-AntigravityProcesses

    $argsList = @($PatcherPy, $op, "--lang", $lang)
    if ($dir) {
        $argsList += @("--dir", $dir)
    }

    Write-Host ""
    Write-Color "正在执行操作 [$op] (语言: $lang)..." Cyan
    & python $argsList
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Color "`n[OK] 操作完成！" Green
        return $true
    } else {
        Write-Color "`n[!] 操作执行遇到错误 (退出码: $exitCode)。" Red
        return $false
    }
}

function Show-IdeGuidance {
    Write-Color "`n--- Antigravity IDE (VS Code) 汉化指引 ---" Cyan
    Write-Host "Antigravity IDE 基于 VS Code 内核构建。"
    Write-Host "若要将配套 IDE 全面汉化为中文，请按照以下步骤操作："
    Write-Color "1. 启动 Antigravity IDE;" Yellow
    Write-Color "2. 按快捷键 Ctrl + Shift + P 呼出命令面板;" Yellow
    Write-Color "3. 输入: Configure Display Language 回车;" Yellow
    Write-Color "4. 选择: 中文 (简体) (zh-cn)；若列表中未预装，选择 Install Additional Languages 并安装 Chinese (Simplified);" Yellow
    Write-Color "5. 重启 IDE 即可生效。" Green
    Write-Host ""
    Read-Host "按回车键返回主菜单..." | Out-Null
}

function Start-AntigravityApp([string]$installDir) {
    if ([string]::IsNullOrWhiteSpace($installDir)) {
        Write-Color "`n未指定安装路径，跳过自动启动。" Yellow
        return
    }

    try {
        $root = (Resolve-Path -LiteralPath $installDir -ErrorAction Stop).ProviderPath
    } catch {
        $root = $installDir
    }

    $exePath = Join-Path $root "Antigravity.exe"
    if (-not (Test-Path -LiteralPath $exePath -PathType Leaf)) {
        Write-Color "`n未在安装路径检测到 Antigravity.exe，跳过自动启动。" Yellow
        return
    }

    if (@(Get-Process -Name 'Antigravity' -ErrorAction SilentlyContinue).Count -gt 0) {
        Write-Color "`n检测到 Antigravity 已在运行中。" Green
        return
    }

    Write-Color "`n正在自动启动 Antigravity..." Green
    try {
        Start-Process -FilePath $exePath -WorkingDirectory $root -ErrorAction Stop
    } catch {
        Write-Color "`n启动 Antigravity 失败：$($_.Exception.Message)" Red
    }
}

function Run-InteractiveMenu {
    $installDir = Find-AntigravityDirectory
    if (-not $installDir) {
        Write-Color "未自动找到 Antigravity 安装目录！" Yellow
        $userDir = (Read-Host "请输入 Antigravity.exe 所在目录路径").Trim().Trim('"')
        if (Test-Path -LiteralPath (Join-Path $userDir "resources\app.asar")) {
            $installDir = $userDir
        } else {
            Write-Color "指定的路径无效，未找到 resources\app.asar！" Red
            Pause
            return
        }
    }

    while ($true) {
        Show-Header
        Write-Color "检测到安装路径: $installDir" DarkCyan
        Write-Host ""
        Write-Color "[1]  安装简体中文补丁 (zh-CN)" Green
        Write-Color "[2]  安装繁体中文补丁 (zh-TW - 台湾)" Green
        Write-Color "[3]  安装繁体中文补丁 (zh-HK - 香港)" Green
        Write-Color "[4]  还原原版 / 卸载补丁 (Restore)" Yellow
        Write-Color "[5]  禁止自动更新 (锁定当前版本)" Magenta
        Write-Color "[6]  恢复自动更新" Magenta
        Write-Color "[7]  查看 Antigravity IDE 汉化指引" Gray
        Write-Color "[8]  开启/配置 版本更新自动维护看门狗 (Auto-Maintainer & GitHub 同步)" Cyan
        Write-Color "[Q]  退出" DarkGray
        Write-Host ""

        $choice = (Read-Host "请选择操作 [1-8 / Q]").Trim().ToUpper()
        switch ($choice) {
            '1' {
                $ok = Invoke-PatchAction "install" "zh-CN" $installDir
                if ($ok) { Start-AntigravityApp $installDir }
                Pause
            }
            '2' {
                $ok = Invoke-PatchAction "install" "zh-TW" $installDir
                if ($ok) { Start-AntigravityApp $installDir }
                Pause
            }
            '3' {
                $ok = Invoke-PatchAction "install" "zh-HK" $installDir
                if ($ok) { Start-AntigravityApp $installDir }
                Pause
            }
            '4' {
                $ok = Invoke-PatchAction "restore" "zh-CN" $installDir
                if ($ok) { Start-AntigravityApp $installDir }
                Pause
            }
            '5' {
                Invoke-PatchAction "disable-updates" "zh-CN" $installDir
                Pause
            }
            '6' {
                Invoke-PatchAction "enable-updates" "zh-CN" $installDir
                Pause
            }
            '7' {
                Show-IdeGuidance
            }
            '8' {
                $watchdogBat = Join-Path $ScriptDir "setup_watchdog.bat"
                if (Test-Path $watchdogBat) {
                    Start-Process cmd.exe -ArgumentList "/c `"$watchdogBat`"" -Wait
                } else {
                    Write-Color "未找到 setup_watchdog.bat 文件。" Red
                    Pause
                }
            }
            'Q' {
                Write-Color "已退出。" Gray
                return
            }
            default {
                Write-Color "输入无效，请重新选择。" Yellow
                Start-Sleep -Seconds 1
            }
        }
    }
}

# 脚本主执行分支
$targetDir = Find-AntigravityDirectory
if ($Action -eq "interactive") {
    Run-InteractiveMenu
} else {
    $ok = Invoke-PatchAction $Action $Language $targetDir
    if ($ok -and ($Action -eq "install" -or $Action -eq "restore")) {
        Start-AntigravityApp $targetDir
    }
}
