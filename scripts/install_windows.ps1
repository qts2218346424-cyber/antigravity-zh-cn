<#
.SYNOPSIS
    Antigravity Windows 简体中文汉化补丁安装/管理脚本
.DESCRIPTION
    参考 claude-desktop-zh-cn 架构设计的 Antigravity 交互式汉化与管理工具。
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
    Write-Color "         (参考 claude-desktop-zh-cn 设计架构)                " DarkGray
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

function Start-DesktopPet {
    $petPy = Join-Path $ProjectRoot "pet\run_pet.py"
    $launcherBat = Join-Path $ProjectRoot "launch-pet.bat"
    if (-not (Test-Path -LiteralPath $petPy)) {
        Write-Color "[!] 未找到 pet\run_pet.py，无法启动桌面小宠物。" Red
        return
    }

    Write-Color "`n正在唤醒 Antigravity 灵动桌面小宠物..." Cyan
    $pyw = Get-Command pythonw -ErrorAction SilentlyContinue
    if ($pyw) {
        Start-Process -FilePath "pythonw" -ArgumentList "`"$petPy`""
    } else {
        Start-Process -FilePath "python" -ArgumentList "`"$petPy`""
    }
    Write-Color "[OK] 桌面小宠物已在后台启动！已挂载系统托盘与桌面浮窗。" Green
}

function Create-PetShortcut {
    $launcherBat = Join-Path $ProjectRoot "launch-pet.bat"
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "Antigravity 桌面宠物.lnk"

    try {
        $wshShell = New-Object -ComObject WScript.Shell
        $shortcut = $wshShell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = $launcherBat
        $shortcut.WorkingDirectory = $ProjectRoot
        $shortcut.Description = "Antigravity 灵动桌面小宠物 (额度感知 / 任务弹窗 / 一键换号)"
        $iconCandidate = Join-Path $ProjectRoot "pet\src-tauri\icons\icon.png"
        if (Test-Path $iconCandidate) {
            $shortcut.IconLocation = $iconCandidate
        }
        $shortcut.Save()
        Write-Color "[OK] 已成功在桌面创建快捷方式: $shortcutPath" Green
    } catch {
        Write-Color "[!] 创建桌面快捷方式失败: $($_.Exception.Message)" Yellow
    }
}

function Ask-DesktopPet {
    $petPy = Join-Path $ProjectRoot "pet\run_pet.py"
    if (-not (Test-Path -LiteralPath $petPy)) { return }

    Write-Host ""
    Write-Color "------------------------------------------------------------" DarkCyan
    Write-Color "✨ 专属特性: Antigravity 灵动桌面小宠物 (Gemini Mascot)" Cyan
    Write-Color "   功能包括: 实时剩余额度感知 / 任务完成弹窗气泡 / 一键多账号无感安全换号" Gray
    Write-Color "------------------------------------------------------------" DarkCyan
    $ans = (Read-Host "是否同时启动 Antigravity 灵动桌面小宠物？[y/n]").Trim().ToLower()
    if ($ans -eq 'y' -or $ans -eq 'yes') {
        Start-DesktopPet
        $scAns = (Read-Host "是否在桌面创建小宠物一键启动快捷方式？[y/n]").Trim().ToLower()
        if ($scAns -eq 'y' -or $scAns -eq 'yes') {
            Create-PetShortcut
        }
    }
}

function Start-AntigravityApp([string]$installDir) {
    $exePath = Join-Path $installDir "Antigravity.exe"
    if (Test-Path -LiteralPath $exePath) {
        $ans = (Read-Host "是否立即启动 Antigravity？[y/n]").Trim().ToLower()
        if ($ans -eq 'y' -or $ans -eq 'yes' -or $ans -eq '') {
            Write-Color "正在启动 Antigravity..." Green
            Start-Process -FilePath $exePath
        }
    }
    Ask-DesktopPet
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
        Write-Color "[1] 安装简体中文补丁 (zh-CN)" Green
        Write-Color "[2] 安装繁体中文补丁 (zh-TW - 台湾)" Green
        Write-Color "[3] 安装繁体中文补丁 (zh-HK - 香港)" Green
        Write-Color "[4] 还原原版 / 卸载补丁 (Restore)" Yellow
        Write-Color "[5] 禁止自动更新 (锁定当前版本)" Magenta
        Write-Color "[6] 恢复自动更新" Magenta
        Write-Color "[7] 查看 Antigravity IDE 汉化指引" Gray
        Write-Color "[8] 开启/配置 版本更新自动维护看门狗 (Auto-Maintainer & GitHub 同步)" Cyan
        Write-Color "[9] 启动 / 管理 Antigravity 灵动桌面小宠物 (额度感知 / 任务弹窗 / 一键换号)" Yellow
        Write-Color "[Q] 退出" DarkGray
        Write-Host ""

        $choice = (Read-Host "请选择操作 [1-9 / Q]").Trim().ToUpper()
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
                Invoke-PatchAction "restore" "zh-CN" $installDir
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
            '9' {
                Write-Color "`n--- Antigravity 灵动桌面小宠物管理 ---" Cyan
                Write-Color "[1] 立即在后台启动小宠物" Green
                Write-Color "[2] 在桌面创建一键启动快捷方式" Green
                Write-Color "[3] 运行 30 项自检冒烟测试 (Smoke Test)" Yellow
                Write-Color "[B] 返回主菜单" Gray
                $sub = (Read-Host "请选择操作 [1/2/3/B]").Trim().ToUpper()
                switch ($sub) {
                    '1' { Start-DesktopPet }
                    '2' { Create-PetShortcut }
                    '3' {
                        $petPy = Join-Path $ProjectRoot "pet\run_pet.py"
                        & python $petPy --smoke
                    }
                }
                Pause
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
    Invoke-PatchAction $Action $Language $targetDir
}
