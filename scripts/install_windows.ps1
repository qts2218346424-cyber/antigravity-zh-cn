<#
.SYNOPSIS
    Antigravity Windows 简体中文汉化补丁安装/管理脚本
.DESCRIPTION
    Antigravity 交互式汉化与管理工具。
#>

[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet("interactive", "install", "restore", "disable-updates", "enable-updates", "uninstall-pet")]
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

function Invoke-PatchAction([string]$op, [string]$lang = "zh-CN", [string]$dir = "", [bool]$withPet = $false) {
    if (-not (Check-PythonEnvironment)) {
        return $false
    }

    Stop-AntigravityProcesses

    $argsList = @($PatcherPy, $op, "--lang", $lang)
    if ($dir) {
        $argsList += @("--dir", $dir)
    }
    if ($op -eq "install") {
        if ($withPet) {
            $argsList += @("--with-pet")
        } else {
            $argsList += @("--no-pet")
        }
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

function Get-PetExecutable {
    $candidates = @(
        (Join-Path $ProjectRoot "pet\pet.exe"),
        (Join-Path $ProjectRoot "pet-wails\build\bin\pet.exe"),
        (Join-Path $ProjectRoot "pet.exe")
    )
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) { return $c }
    }
    return $null
}

function Start-DesktopPet {
    $petExe = Get-PetExecutable
    if ($petExe) {
        Write-Color "`n正在以 Go 原生秒开引擎唤醒 Antigravity 灵动桌面小宠物..." Green
        Start-Process -FilePath $petExe
        Write-Color "[OK] 桌面小宠物已在后台极速启动！DirectComposition 硬件级透明已就绪。" Green
        return
    }

    $petPy = Join-Path $ProjectRoot "pet\run_pet.py"
    if (-not (Test-Path -LiteralPath $petPy)) {
        Write-Color "[!] 未找到 pet.exe 或 pet\run_pet.py，无法启动桌面小宠物。" Red
        return
    }

    Write-Color "`n正在唤醒 Antigravity 灵动桌面小宠物 (Python 回退模式)..." Cyan
    $pyw = Get-Command pythonw -ErrorAction SilentlyContinue
    if ($pyw) {
        Start-Process -FilePath "pythonw" -ArgumentList "`"$petPy`""
    } else {
        Start-Process -FilePath "python" -ArgumentList "`"$petPy`""
    }
    Write-Color "[OK] 桌面小宠物已在后台启动！已挂载系统托盘与桌面浮窗。" Green
}

function Create-PetShortcut {
    $petExe = Get-PetExecutable
    $launcherBat = Join-Path $ProjectRoot "launch-pet.bat"
    $desktopPath = [Environment]::GetFolderPath("Desktop")
    $shortcutPath = Join-Path $desktopPath "Antigravity 桌面宠物.lnk"

    try {
        $wshShell = New-Object -ComObject WScript.Shell
        $shortcut = $wshShell.CreateShortcut($shortcutPath)
        if ($petExe) {
            $shortcut.TargetPath = $petExe
            $shortcut.WorkingDirectory = Split-Path -Parent $petExe
            $shortcut.IconLocation = "$petExe,0"
        } else {
            $shortcut.TargetPath = $launcherBat
            $shortcut.WorkingDirectory = $ProjectRoot
            $iconCandidate = Join-Path $ProjectRoot "pet\src-tauri\icons\icon.png"
            if (Test-Path $iconCandidate) {
                $shortcut.IconLocation = $iconCandidate
            }
        }
        $shortcut.Description = "Antigravity 灵动桌面小宠物 (额度感知 / 任务弹窗 / 一键换号)"
        $shortcut.Save()
        Write-Color "[OK] 已成功在桌面创建快捷方式: $shortcutPath" Green
    } catch {
        Write-Color "[!] 创建桌面快捷方式失败: $($_.Exception.Message)" Yellow
    }
}

function Ask-DesktopPet {
    $petExe = Get-PetExecutable
    $petPy = Join-Path $ProjectRoot "pet\run_pet.py"
    if ((-not $petExe) -and (-not (Test-Path -LiteralPath $petPy))) { return }

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

function Start-AntigravityApp([string]$installDir, [bool]$promptPet = $false) {
    $exePath = Join-Path $installDir "Antigravity.exe"
    if (Test-Path -LiteralPath $exePath) {
        $ans = (Read-Host "是否立即启动 Antigravity？[y/n]").Trim().ToLower()
        if ($ans -eq 'y' -or $ans -eq 'yes' -or $ans -eq '') {
            Write-Color "正在启动 Antigravity..." Green
            Start-Process -FilePath $exePath
        }
    }
    if ($promptPet) {
        Ask-DesktopPet
    }
}

function Ask-PetOption {
    Write-Host ""
    Write-Color "请选择桌面宠物安装配置:" Cyan
    Write-Color "  [1] 安装汉化 + Go 原生灵动桌面小宠物 (推荐全能版，秒开硬件级透明)" Green
    Write-Color "  [2] 仅安装纯净汉化补丁 (不包含桌面小宠物)" Gray
    $ans = (Read-Host "请选择 [1/2] (直接回车默认: 1)").Trim()
    if ($ans -eq "2") {
        return $false
    }
    return $true
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
        Write-Color "[1]  安装简体中文补丁 (zh-CN，支持选择纯净版或全能桌宠版)" Green
        Write-Color "[2]  安装繁体中文补丁 (zh-TW - 台湾，支持选择桌宠)" Green
        Write-Color "[3]  安装繁体中文补丁 (zh-HK - 香港，支持选择桌宠)" Green
        Write-Color "[4]  单独安装/挂载桌面小宠物到 Antigravity (开启伴随自启，免重装)" Cyan
        Write-Color "[5]  还原原版 / 卸载补丁 (Restore)" Yellow
        Write-Color "[6]  禁止自动更新 (锁定当前版本)" Magenta
        Write-Color "[7]  恢复自动更新" Magenta
        Write-Color "[8]  查看 Antigravity IDE 汉化指引" Gray
        Write-Color "[9]  开启/配置 版本更新自动维护看门狗 (Auto-Maintainer & GitHub 同步)" Cyan
        Write-Color "[10] 桌面宠物专区 (启动 / 安装 / 快捷方式 / 重新编译 / 卸载)" Yellow
        Write-Color "[Q]  退出" DarkGray
        Write-Host ""

        $choice = (Read-Host "请选择操作 [1-10 / Q]").Trim().ToUpper()
        switch ($choice) {
            '1' {
                $withPet = Ask-PetOption
                $ok = Invoke-PatchAction "install" "zh-CN" $installDir $withPet
                if ($ok) { Start-AntigravityApp $installDir $withPet }
                Pause
            }
            '2' {
                $withPet = Ask-PetOption
                $ok = Invoke-PatchAction "install" "zh-TW" $installDir $withPet
                if ($ok) { Start-AntigravityApp $installDir $withPet }
                Pause
            }
            '3' {
                $withPet = Ask-PetOption
                $ok = Invoke-PatchAction "install" "zh-HK" $installDir $withPet
                if ($ok) { Start-AntigravityApp $installDir $withPet }
                Pause
            }
            '4' {
                $ok = Invoke-PatchAction "install-pet" "zh-CN" $installDir $false
                if ($ok) {
                    Create-PetShortcut
                    Start-DesktopPet
                }
                Pause
            }
            '5' {
                Invoke-PatchAction "restore" "zh-CN" $installDir
                Pause
            }
            '6' {
                Invoke-PatchAction "disable-updates" "zh-CN" $installDir
                Pause
            }
            '7' {
                Invoke-PatchAction "enable-updates" "zh-CN" $installDir
                Pause
            }
            '8' {
                Show-IdeGuidance
            }
            '9' {
                $watchdogBat = Join-Path $ScriptDir "setup_watchdog.bat"
                if (Test-Path $watchdogBat) {
                    Start-Process cmd.exe -ArgumentList "/c `"$watchdogBat`"" -Wait
                } else {
                    Write-Color "未找到 setup_watchdog.bat 文件。" Red
                    Pause
                }
            }
            '10' {
                $petExe = Get-PetExecutable
                Write-Color "`n--- Antigravity 灵动桌面小宠物专区 ---" Cyan
                if ($petExe) {
                    Write-Color "当前引擎: Go 原生 DirectComposition 硬件透明加速 [就绪: $petExe]" Green
                } else {
                    Write-Color "当前引擎: Python 解释执行模式 (建议编译 Go 原生单文件)" Yellow
                }
                Write-Color "[1] 立即在后台启动小宠物 (优先原生引擎)" Green
                Write-Color "[2] 安装并挂载桌面宠物自启 Hook 到 Antigravity (开启伴随自启)" Cyan
                Write-Color "[3] 在桌面创建一键启动快捷方式" Green
                Write-Color "[4] 重新编译生成 Go 原生单文件 pet.exe" Cyan
                Write-Color "[5] 运行完整自检与回归测试" Yellow
                Write-Color "[6] 彻底卸载桌面宠物 (清除自启 Hook、关闭后台进程、删除快捷方式与沙盒)" Red
                Write-Color "[B] 返回主菜单" Gray
                $sub = (Read-Host "请选择操作 [1/2/3/4/5/6/B]").Trim().ToUpper()
                switch ($sub) {
                    '1' { Start-DesktopPet }
                    '2' {
                        $ok = Invoke-PatchAction "install-pet" "zh-CN" $installDir $false
                        if ($ok) {
                            Create-PetShortcut
                            Start-DesktopPet
                        }
                    }
                    '3' { Create-PetShortcut }
                    '4' {
                        $wailsDir = Join-Path $ProjectRoot "pet-wails"
                        if (Test-Path $wailsDir) {
                            Write-Color "`n正在调用 Wails 极速构建 Go 原生桌面小宠物..." Cyan
                            Push-Location $wailsDir
                            & wails build
                            Pop-Location
                            $builtExe = Join-Path $wailsDir "build\bin\pet.exe"
                            if (Test-Path $builtExe) {
                                Copy-Item -Path $builtExe -Destination (Join-Path $ProjectRoot "pet\pet.exe") -Force
                                Write-Color "[OK] 编译并分发成功！已同步至 pet\pet.exe" Green
                            }
                        } else {
                            Write-Color "未找到 pet-wails 源码目录。" Red
                        }
                    }
                    '5' {
                        $petPy = Join-Path $ProjectRoot "pet\run_pet.py"
                        if (Test-Path $petPy) {
                            & python $petPy --smoke
                        }
                    }
                    '6' {
                        Invoke-PatchAction "uninstall-pet" "zh-CN" $installDir
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
