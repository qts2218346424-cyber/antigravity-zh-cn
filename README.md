# Antigravity 简体中文汉化项目 (antigravity-zh-cn)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-blue.svg)](#适用环境)
[![Target](https://img.shields.io/badge/Target-Google%20Antigravity-green.svg)](https://antigravity.google)

一个专为 **Google Antigravity**（智能体桌面端与配套 IDE）打造的高性能本地中文汉化补丁与辅助工具。

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
  - **真实双轨配额对齐**：官方通道直连，精准同步呈现 Gemini (5h / 每周) 与 Claude/GPT (5h / 每周) 双轨配额百分比与恢复倒计时，5 分钟懒加载安全防限流；
  - **彻底防连击崩溃**：点击与 Win32 原生拖拽彻底解耦，位移 > 5px 才触发拖动，纯点击 0 模态消息冲突，连击 100 次丝滑稳定；
  - **弹窗自动消失与防遮挡**：单实例限制（绝不堆叠 3 层），2 秒平滑消失，400ms 离开宽限，形象切换零遮脸（改为头顶气泡对白）；
  - **随主程序安全自启**：随 Antigravity 启动自动无感拉起，界面设置面板与系统托盘提供双向一键开关；
  - **一键便携安全换号**：底层采用 Win32 原生原子替换，多 Profile 毫秒级无感安全切换；
  - **Awesome Codex Pet 生态支持**：纯透明无边框漫步，内置派蒙、哆啦A梦等多款热门桌宠，支持任意 GIF/WebP/PNG/SVG 拖放热替换。
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
   [1]  安装简体中文纯净补丁 (zh-CN，仅汉化，不附带桌面宠物)
   [2]  安装简体中文全能补丁 (zh-CN，汉化 + 灵动桌面小宠物)
   [3]  安装繁体中文纯净补丁 (zh-TW - 台湾)
   [4]  安装繁体中文纯净补丁 (zh-HK - 香港)
   [5]  还原原版 / 卸载补丁 (Restore)
   [6]  禁止自动更新 (锁定当前版本)
   [7]  恢复自动更新
   [8]  查看 Antigravity IDE 汉化指引
   [9]  开启/配置 版本更新自动维护看门狗 (Auto-Maintainer & GitHub 同步)
   [10] 桌面宠物专区 (启动 / 创建快捷方式 / 彻底卸载与清理)
   [Q]  退出
   ```
5. **可选方案（自主选择）**：
   - **纯净汉化补丁**：输入 `1` 回车，仅对 Antigravity 注入中文语言包与 DOM 翻译引擎，**100% 纯净无捆绑**，绝不注入任何桌宠自启代码；
   - **全能汉化补丁**：输入 `2` 回车，汉化同时挂载灵动桌面小宠物，支持实时官方双轨配额监控与一键换号；
6. 提示完成后会询问是否立即启动 Antigravity。

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

## 桌面宠物可选方案与彻底卸载指南

为了尊重不同用户的使用习惯，本项目实现了汉化补丁与桌面宠物的**完全解耦**：

### 1. 想要纯净汉化，不想要桌面宠物？
- 在安装控制台直接选择 **`[1] 安装简体中文纯净补丁`**（或命令行执行 `python scripts/patch_antigravity.py install --no-pet`）；
- 核心补丁引擎绝不会在 `app.asar` 中注入任何桌宠自启 Hook，绝不后台拉起任何宠物守护进程。

### 2. 之前安装了桌面宠物，后续希望彻底卸载？
随时可以一键彻底卸载并无损保留汉化：
- **方式一（交互式控制台）**：双击运行 `install-windows.bat`，输入 `10` 进入桌面宠物专区，选择 `[4] 彻底卸载桌面宠物`；
- **方式二（命令行直达）**：
  ```bash
  python scripts/patch_antigravity.py uninstall-pet
  ```
- **卸载执行效果**：
  - 🛑 自动安全终止运行中的桌面宠物后台进程；
  - ✂️ 自动从 `app.asar` 的 `dist/utils.js` 中彻底剥离自启 Hook，完美还原为纯净汉化（无需重新打汉化补丁）；
  - ⚙️ 将配置中的自启动状态永久置为 `false`；
  - 🗑️ 自动扫描并清理桌面快捷方式；
  - 🧹 清除临时渲染沙盒缓存（`~/.gemini/pet_webview_data`）。

### 3. 运行中临时停用或关闭自启？
- 在桌宠右侧托盘图标右键菜单中，点击 **`随 Antigravity 启动自动运行`**（取消勾选），或直接点击 **`彻底退出并关闭自启动`**。

---

## Antigravity 灵动桌面小宠物 (Gemini Mascot)

为了让开发者拥有更愉悦、更可控的编码体验，本项目深度整合了纯原生、超轻量、无任何黑灰边框的**灵动桌面小宠物**（位于 `pet/` 目录），参考了开源项目 [Awesome Codex Pet](https://github.com/legeling/awesome-codex-pet) 的优秀视觉体验。

### ✨ 核心功能亮点
- 🐾 **全透明灵动漫步**：采用 Windows DWM 硬件透明层，完全消除背景框与多余遮挡，宠物自然漫步于桌面。
- 📊 **真实官方双轨配额 100% 对齐**：
  - 直连 Antigravity 官方接口，准确同步登录用户（名称、头像、邮箱）；
  - **Gemini 模型组 (Flash, Pro)**：专属 5 小时配额与每周配额进度条（健康绿 / 告警黄 / 紧急红）及绝对恢复时间；
  - **Claude & GPT 顶级模型组 (Sonnet, Opus, GPT-OSS)**：专属 5 小时配额与每周配额进度；
  - 配额 5 分钟懒加载安全缓存，严禁高频轮询，杜绝 429 被限流风险。
- 🛡️ **彻底根除连击崩溃 Bug**：
  - 点击与 Win32 原生拖拽彻底解耦：`mousedown` 仅记录坐标，仅当在屏幕上物理位移 > 5px 时才判定为拖拽；
  - 纯点击互动走纯轻量逻辑，**0 Win32 消息循环介入**，彻底告别频繁敲击导致的闪退崩溃；
  - 后端内置 200ms 单调时钟互斥锁（`threading.Lock`），高频并发安全降级；全局命名互斥锁严格保证单实例运行。
- 🔔 **弹窗 2 秒自动平滑消失（告别遮脸与永不消失）**：
  - 严格限制单实例展示，新通知即刻替换旧通知，绝不重叠堆叠 3 层；
  - 2.0 秒平滑渐隐，鼠标离开 400ms 宽限期，3.5 秒硬超时安全熔断；
  - 形象切换零遮挡：移除了切换形象时的全局弹窗，改为宠物头顶轻快自空气泡。
- 🚀 **按需自启与一键彻底卸载**：
  - 仅在用户选择全能版补丁时注入安全守护逻辑；
  - 提供一键彻底卸载与自启剥离支持，随时可在纯净版与全能版之间自由切换。
- ⚡ **一键便携安全换号**：底层基于 Windows 原生 Win32 `MoveFileExW` 硬件级原子替换协议与微秒级防碰撞备份，多套账号配置一键无感切换，断电亦可自动安全回滚。
- 🎨 **Awesome Codex Pet 生态支持**：内置 Gemini 灵动像素星灵、派蒙、哆啦A梦等多款热门预设，支持直接拖放本地任意 PNG / GIF / WebP / SVG 瞬间换装。

### 🚀 启动与使用
- **随 Antigravity 自启**：选择全能汉化补丁后生效，打开 Antigravity 即可自动拉起；
- **独立管理**：通过汉化菜单 `[10] 桌面宠物专区` 随时启动、创建快捷方式或彻底卸载；
- **独立运行**：双击根目录下的 `launch-pet.bat` 即可静默启动；
- **自动化测试验证**：
  ```bash
  python pet/run_pet.py --smoke          # 32 项自检冒烟测试 (100% PASS)
  python -m unittest pet/tests/test_v2_features.py  # 核心并发防崩与双轨配额专项测试
  python -m unittest discover -s pet/tests -p "test_*.py"  # 57 项全量端到端与对抗测试
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
