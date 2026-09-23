# Antigravity 简体中文汉化项目 (antigravity-zh-cn)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](#适用环境)
[![Target](https://img.shields.io/badge/Target-Google%20Antigravity-green.svg)](https://antigravity.google)

一个专为 **Google Antigravity**（智能体桌面端与配套 IDE）打造的高性能本地中文汉化补丁与辅助工具，参考了社区知名项目 `javaht/claude-desktop-zh-cn` 的架构设计。

支持 **简体中文 (zh-CN)**、**繁体中文（中国台湾 zh-TW）** 和 **繁体中文（中国香港 zh-HK）**。

---

## 目录

- [功能特点](#功能特点)
- [适用环境](#适用环境)
- [使用方法](#使用方法)
  - [Windows](#windows)
  - [macOS](#macos)
  - [Linux](#linux)
- [Antigravity 灵动桌面小宠物 (Gemini Mascot)](#antigravity-灵动桌面小宠物-gemini-mascot)
- [Antigravity IDE 汉化说明](#antigravity-ide-汉化说明)
- [技术原理与架构](#技术原理与架构)
- [开发者指南：词条抽取与更新](#开发者指南词条抽取与更新)
- [常见问题 (FAQ)](#常见问题-faq)
- [免责声明](#免责声明)

---

## 功能特点

- **双层全景汉化**：
  - **原生壳层 (Electron Main)**：汉化窗口顶栏菜单（`menu.js`）、系统托盘菜单（`tray.js`）、更新状态提示（`updater.js`）及 WSL 连接菜单。
  - **渲染层 (Agent Web UI)**：通过 Preload 预加载注入高性能微型 DOM 翻译引擎，汉化全部会话、工件面板 (Artifacts)、设置中心、模型选择、差异比对 (Diff)、运行状态提示等。
- **🐱 灵动桌面小宠物 (Gemini Mascot)**：
  - **额度实时感知**：悬浮挂件实时探测本地 `~/.gemini` 模型剩余额度与调用频次；
  - **任务弹窗提醒**：长时间后台编码任务完成或异常报错时，触发轻量非抢占式气泡通知；
  - **一键便携换号**：底层采用 Win32 原生原子替换，多 Profile 毫秒级无感安全切换；
  - **形象自主定义**：默认搭载 Gemini 吉祥物，支持用户导入 PNG/GIF/WebP/SVG 自定义形象并热切换。
- **智能代码与输入保护**：
  - 核心引擎严格排除代码编辑器（Monaco Editor / CodeMirror）、`<pre>`、`<code>`、终端容器（XTerm）、用户输入框（`contenteditable` / `textarea`）以及对话正文区域，**绝对不会篡改任何代码逻辑或用户输入内容**。
- **流式防抖与截止时间控制**：
  - 针对 AI 流式打字机输出进行节流监视（最长截止保护 250ms），既保证了界面的实时中文响应，又彻底杜绝了高频 DOM 变更引发的掉帧卡顿。
- **多语言变体一键切换**：
  - 支持 `zh-CN`（简体中文）、`zh-TW`（繁体中文-台湾）、`zh-HK`（繁体中文-香港）。
- **安全备份与一键无损还原**：
  - 首次安装自动创建 `app.asar.bak` 原始副本；随时可通过控制台选择 `还原` 恢复官方原貌。
- **更新管理支持**：
  - 内置禁止/恢复官方自动更新的快捷开关，防止应用静默升级覆盖汉化。

---

## 适用环境

| 操作系统 | 支持情况 | 依赖要求 |
| :--- | :--- | :--- |
| **Windows** | ✅ 完美支持 (Windows 10 / 11) | 系统自带 PowerShell，建议已安装 Python 3 |
| **macOS** | ✅ 支持 (Apple Silicon & Intel) | 系统自带 `python3`，执行脚本自动处理 ad-hoc 签名 |
| **Linux** | ✅ 支持 (Ubuntu/Debian 等主流发行版) | 系统自带 `python3` |

---

## 使用方法

### Windows

1. 退出正在运行的 Antigravity；
2. 下载或克隆本项目到本地；
3. **鼠标双击运行 `install-windows.bat`**；
   - 脚本会自动请求管理员权限（弹出 UAC 提权提示）；
4. 在弹出的交互控制台中按数字键选择：
   ```text
   ============================================================
            Antigravity 简体中文汉化补丁管理器
   ============================================================
   [1] 安装简体中文补丁 (zh-CN)
   [2] 安装繁体中文补丁 (zh-TW - 台湾)
   [3] 安装繁体中文补丁 (zh-HK - 香港)
   [4] 还原原版 / 卸载补丁 (Restore)
   [5] 禁止自动更新 (锁定当前版本)
   [6] 恢复自动更新
   [7] 查看 Antigravity IDE 汉化指引
   [8] 开启/配置 版本更新自动维护看门狗 (Auto-Maintainer & GitHub 同步)
   [9] 启动 / 管理 Antigravity 灵动桌面小宠物 (额度感知 / 任务弹窗 / 一键换号)
   [Q] 退出
   ```
5. 输入 `1` 回车，等待 2-5 秒即可完成汉化；
6. 提示完成后会询问是否立即启动 Antigravity，并可**一键同步唤醒 Antigravity 灵动桌面小宠物**并创建桌面快捷方式！

### macOS

1. 退出 Antigravity；
2. 打开终端，进入本项目目录；
3. 执行 `./install-mac.command`（或在访达中双击 `install-mac.command`）；
4. 选择对应的中文语言选项；
5. 脚本自动备份、解包打补丁，并执行本机 ad-hoc 重签名，防止 macOS 安全拦截。

### Linux

1. 退出 Antigravity；
2. 在终端运行：
   ```bash
   chmod +x install-linux.sh
   ./install-linux.sh
   ```
3. 按屏幕提示选择所需功能。

---

## Antigravity 灵动桌面小宠物 (Gemini Mascot)

为了让开发者拥有更愉悦、更可控的编码体验，本项目附带了纯原生、超轻量的**灵动桌面小宠物**（位于 `pet/` 目录）。

### ✨ 核心功能亮点
- 🐾 **透明悬浮交互**：默认以可爱的 Gemini 蓝色能量吉祥物形态悬浮于桌面，支持自由拖拽、位置持久化、置顶切换与最小化到托盘。
- 📊 **额度实时监控**：自动感知本地 `~/.gemini` 模型调用额度，通过宠物表情与小徽标实时反映剩余配额，免去反复登入网页查询。
- 🔔 **任务完成与告警弹窗**：在复杂长耗时编码任务完成或构建出现错误时，触发不抢焦点的轻量桌面气泡提示。
- ⚡ **一键便携安全换号**：底层基于 Windows 原生 Win32 `MoveFileExW` 硬件级原子替换协议与微秒级防碰撞备份，多套账号配置（`work`, `personal`, `dev` 等）一键无感切换，断电亦可自动安全回滚。
- 🎨 **形象自主定义**：支持导入个人专属透明背景图片（`.png`, `.gif`, `.webp`, `.svg`）进行热替换，并内置了星芒晶体、量子机甲、星系能量球等多套主题预设。

### 🚀 启动与使用
- **随汉化一键启动**：运行 `install-windows.bat` 完成汉化时直接按提示开启；
- **桌面快捷方式**：可通过汉化菜单 `[9]` 在桌面生成专属启动图标；
- **独立运行**：双击根目录下的 `launch-pet.bat` 即可静默启动；
- **自动化测试验证**：
  ```bash
  python pet/run_pet.py --smoke          # 30 项自检冒烟测试
  python pet/test_account_switcher.py    # 98 项全量端到端测试
  ```

---

## Antigravity IDE 汉化说明

Antigravity 套件中配套的 **Antigravity IDE**（代码编辑器）基于 VS Code 架构。如需将该编辑器汉化：

1. 启动 **Antigravity IDE**；
2. 按快捷键 `Ctrl + Shift + P`（macOS 为 `Cmd + Shift + P`）打开命令面板；
3. 输入并选择：`Configure Display Language`（配置显示语言）；
4. 在下拉列表中选择：`中文 (简体) (zh-cn)`；
   - 若列表中未列出，选择 `Install Additional Languages...`，在左侧扩展市场搜索并安装 `Chinese (Simplified)` 官方中文语言包；
5. 根据提示点击 **Restart** 重启 IDE 即可。

---

## 技术原理与架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Google Antigravity                       │
│                                                             │
│  ┌───────────────────────┐       ┌───────────────────────┐  │
│  │   Electron Shell      │       │     Agent Web UI      │  │
│  │   (resources/app.asar)│       │  (Language Server:LS) │  │
│  │                       │       │                       │  │
│  │  • menu.js (主菜单)    │       │  • 对话面板 & 输入框   │  │
│  │  • tray.js (系统托盘)  │       │  • Artifacts 工件视图 │  │
│  │  • updater.js (更新器) │       │  • 任务规划与执行确认  │  │
│  │  • preload.js (预加载) │       │  • 全局设置与模型选择 │  │
│  └───────────┬───────────┘       └───────────▲───────────┘  │
│              │                               │              │
│              │ Injects Runtime Engine        │              │
│              └───────────────────────────────┘              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                               ▲
                               │
            ┌──────────────────┴──────────────────┐
            │       antigravity-zh-cn 补丁包       │
            ├─────────────────────────────────────┤
            │ • patch_antigravity.py (补丁核心)    │
            │ • runtime-zh.js (DOM 遍历与监听引擎)│
            │ • auto_maintainer.py (自动化引擎)   │
            │ • antigravity-zh-CN.json (界面词典) │
            │ • desktop-zh-CN.json (外壳词典)     │
            │ • rules-zh-CN.json (动态正则规则)   │
            └─────────────────────────────────────┘
```

1. **ASAR 智能处理**：内置原生 Python ASAR 编解码器（同时兼容检测并调用系统 `npx asar`），实现无损解包与重封；
2. **Preload 无感桥接**：在 Electron 的 `preload.js` 启动阶段载入词典并注入微型翻译器；
3. **高效率 DOM 替换**：
   - 使用现代浏览器原生的 `TreeWalker` 单向流式检索文本节点，开销控制在毫秒级；
   - 对动态新增的 DOM（例如 AI 回复、折叠菜单、弹窗），利用 `MutationObserver` 结合时间窗口截流（Max Deadline 250ms）处理。

---

## 全自动版本跟踪与 GitHub 持续维护 (Auto-Maintainer)

为了让开源项目在 Google 官方发布新版时能够**无人值守自动同步维护**，本项目内置了**双轨自动化维护系统**：

### 1. 本地无人值守看门狗 (`scripts/setup_watchdog.bat`)
- 双击运行 `scripts/setup_watchdog.bat` 并按 `1`，即可一键注册 Windows 后台计划任务；
- 任务每小时静默检测本地 Antigravity 是否发生版本更新（如 2.16.0 升级至 2.17.0）；
- 一旦检测到新版发布或程序被官方覆盖，脚本会自动：
  1. 深度拉取新版 Bundle 并提取新增英文词条；
  2. 自动增量翻译、同步繁体并运行测试集；
  3. 为新版本原位重打补丁，并执行 `git commit` 与 `git push origin main` 自动同步至您的 GitHub 仓库！

### 2. GitHub Actions 云端定时巡检 (`.github/workflows/auto-update.yml`)
- 仓库已内置 CI/CD 定时工作流，每 6 小时在 GitHub 云端自动轮询 Google 官方版本清单；
- 发现版本升级时，云端 Runner 自动编译校验词库并生成提交推送，保持远程仓库始终与官方最新版本同步。

---

## 开发者指南：词条抽取与更新

当 Antigravity 发布大版本更新导致界面新增英文词条时，维护者亦可手动执行自动化流水线：

```bash
# 一键执行全自动维护（检测、提取、翻译、测试、打补丁与推送）
python scripts/auto_maintainer.py

# 或者手动抽取词条对比：
python scripts/extract_strings.py
```

翻译 `untranslated.json` 中的新词条后，合并入 `resources/antigravity-zh-CN.json` 并提交 Pull Request 即可！

---

## 常见问题 (FAQ)

#### Q: 汉化后会影响代码生成或终端命令吗？
**不会**。我们的 DOM 引擎设置了多重白名单防线，代码编辑器区、Terminal 终端流、Markdown 代码块、用户输入框均被严格保护，只有按钮、标签、菜单等 UI 界面元素才会被中文化。

#### Q: 为什么重启应用后汉化会掉？更新软件版本后会掉吗？
**原因分析**：Google 官方客户端内置了后台静默更新机制（Electron autoUpdater），默认会在后台静默轮询并下载官方全量更新包（`installer.exe`）到 `%LOCALAPPDATA%\antigravity-updater\pending` 中。当用户退出或重启 Antigravity 时，更新器会自动执行静默覆盖安装，将整个安装目录及 `resources/app.asar` 还原为 Google 官方未汉化版。

**最新版本的永久解决方案**：
1. **自动禁用静默更新**：最新补丁安装时，已默认将 `dist/updater.js` 中的 `autoDownload` 与 `autoInstallOnAppQuit` 关闭，从代码底层阻断静默下载；
2. **清空并阻断静默缓存**：自动将 `app-update.yml` 重命名为 `app-update.yml.disabled`，并彻底清空本地残留的静默安装包，确保重启再也不会被静默覆盖；
3. **版本升级后一键重打**：若未来您主动选择升级了新版 Antigravity，只需鼠标双击 `install-windows.bat` 按 `1`，2 秒内即可全自动无损重装最新汉化！

#### Q: 如何彻底卸载汉化补丁？
运行安装脚本并选择选项 `[4] 还原原版 / 卸载补丁`，程序会自动将 `app.asar.bak` 恢复为原样，没有任何残留文件。

---

## 免责声明

1. 本项目为开源社区第三方本地化辅助项目，与 Google 官方无关；
2. 汉化逻辑仅在本地对界面显示文本进行本地化修饰，不收集任何用户隐私数据，亦不修改任何网络通信与模型请求。
