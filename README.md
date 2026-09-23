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
   [Q] 退出
   ```
5. 输入 `1` 回车，等待 2-5 秒即可完成汉化；
6. 提示完成后会询问是否立即启动 Antigravity，直接回车即可畅享中文界面！

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

## 开发者指南：词条抽取与更新

当 Antigravity 发布大版本更新导致界面新增英文词条时，维护者可以通过内置工具轻松提取并补全翻译：

```bash
# 1. 确保 Antigravity 正在运行
# 2. 执行词条抽取工具：
python scripts/extract_strings.py

# 脚本会自动连接当前实例，抽取全部界面候选词条，
# 并与现有词典对比，输出尚未翻译的内容到 resources/untranslated.json
```

翻译 `untranslated.json` 中的新词条后，合并入 `resources/antigravity-zh-CN.json` 并提交 Pull Request 即可！

---

## 常见问题 (FAQ)

#### Q: 汉化后会影响代码生成或终端命令吗？
**不会**。我们的 DOM 引擎设置了多重白名单防线，代码编辑器区、Terminal 终端流、Markdown 代码块、用户输入框均被严格保护，只有按钮、标签、菜单等 UI 界面元素才会被中文化。

#### Q: Antigravity 自动更新后汉化失效了怎么办？
官方自动更新会下载全新的 `app.asar` 覆盖本地目录。若更新后界面变为英文：
- 重新运行 `install-windows.bat`（或对应系统脚本），按 `1` 重新安装即可；
- 或者使用菜单选项 `5` 禁止自动更新，锁定当前版本。

#### Q: 如何彻底卸载汉化补丁？
运行安装脚本并选择选项 `[4] 还原原版 / 卸载补丁`，程序会自动将 `app.asar.bak` 恢复为原样，没有任何残留文件。

---

## 免责声明

1. 本项目为开源社区第三方本地化辅助项目，与 Google 官方无关；
2. 汉化逻辑仅在本地对界面显示文本进行本地化修饰，不收集任何用户隐私数据，亦不修改任何网络通信与模型请求。
