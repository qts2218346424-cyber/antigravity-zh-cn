#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Settings & UI Dictionary Completer for Antigravity
Translates all settings descriptions, options, and missing UI elements.
"""

import sys
import json
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SETTINGS_TRANSLATIONS = {
    # Sidebar & navigation
    "Show Less": "收起",
    "Show More": "展开更多",
    "Not in Project": "未归入项目",
    "In Project": "项目内",
    "Collapse": "折叠",
    "Expand": "展开",
    "Configure in Settings": "在设置中配置",
    "Manage in Settings": "在设置中管理",
    "Open in Settings": "在设置中打开",
    "General Settings": "通用设置",
    "Application Settings": "应用程序设置",
    "Appearance Settings": "外观设置",
    "Model Settings": "模型设置",
    "Customization Settings": "自定义配置设置",
    "Browser Settings": "内置浏览器设置",
    "Terminal Settings": "终端设置",

    # Settings Descriptions & Helper Texts
    "A Gemini-powered security agent decides if commands should be auto-approved.": "由 Gemini 驱动的安全代理智能评估命令是否可以自动批准执行。",
    "A label for this computer when you connect from another device. Changing it reconnects.": "从其他设备连接时用于标识此电脑的标签。更改后将重新建立连接。",
    "A nickname for identifying this application in the companion website. Changing this will restart the connection.": "在配套网站中用于标识此应用程序的昵称。更改此项将重启连接。",
    "A shell setup script run before every command the agent executes in this project. Overrides the global script.": "Agent 在此项目中执行每条命令前运行的 Shell 初始化脚本（覆盖全局脚本）。",
    "A shell setup script run before every command the agent executes.": "Agent 执行每条命令前预先运行的全局 Shell 初始化脚本。",
    "ABFS Workspace (Alpha)": "ABFS 工作区 (Alpha 测试版)",
    "Agent always asks for review.": "Agent 在执行前始终请求人工审查。",
    "Allow sandboxed commands to make network requests.": "允许沙盒环境中的命令发起外网请求。",
    "Allow the agent to run without restrictions.": "允许 Agent 无限制自由运行（不推荐在生产环境中使用）。",
    "Allow/deny agent browser actuation access to specific URLs.": "允许/拒绝 Agent 浏览器操作访问特定的 URL 地址。",
    "Allow/deny agent command execution outside the sandbox.": "允许/拒绝 Agent 在沙盒外直接执行特定命令。",
    "Allow/deny agent read access to specific URLs or domains.": "允许/拒绝 Agent 读取特定 URL 或域名的网页内容。",
    "Allow/deny agent read access to specific files or directories.": "允许/拒绝 Agent 读取特定文件或目录路径。",
    "Allow/deny agent write access to specific files or directories.": "允许/拒绝 Agent 写入或修改特定文件或目录路径。",
    "Allow/deny specific terminal commands.": "允许/拒绝 Agent 执行特定的终端命令。",
    "Allows the agent to access files outside of your current workspace.": "允许 Agent 访问当前工作区目录之外的文件系统内容。",
    "Ask a quick question without interrupting the main conversation.": "快速提出问题，无需打断主对话流程。",
    "Ask for permission for sensitive operations.": "在执行敏感操作前主动向用户索取权限许可。",
    "Automatically expand the Changes Overview toolbar when the agent finishes generating a response.": "当 Agent 完成响应生成后，自动展开“更改概览”工具栏。",
    "Automatically prompt you to restart the app when a new update is available. When disabled, you can check for updates manually from the app menu.": "当发现新版本时自动提示重启应用。禁用后，您仍可在应用菜单中手动检查更新。",
    "Browse and enable plugins from the Build With Google catalog.": "浏览并启用来自 Build With Google 目录的官方扩展插件。",
    "Choose how technical the interface should be.": "选择界面所展示的技术细节深度与专业程度。",
    "Choose the product skin that fits how you work.": "选择契合您日常工作流的产品外观皮肤。",
    "Click to go there, drag to select a range, drag an edge to resize": "点击跳转，拖动选择范围，拖动边缘调整大小",
    "Clone current workspace into a new independent workspace": "将当前工作区克隆为全新的独立工作区",
    "Command and file access granted to the automation agents.": "授予自动化 Agent 的命令行与文件系统访问权限。",
    "Commands the agent can run outside the sandbox in this workspace.": "Agent 在当前工作区中可在沙盒外运行的命令列表。",
    "Commands the agent can run outside the sandbox.": "Agent 可在沙盒保护外直接运行的命令列表。",
    "Configure GitHub access policies.": "配置 GitHub 的仓库访问与授权策略。",
    "Configure agent execution, queued message delivery, and permissions.": "配置 Agent 执行模式、排队消息发送机制及运行权限。",
    "Configure allowed and denied URLs for browser actuation.": "配置浏览器操作允许与拒绝访问的 URL 规则列表。",
    "Configure allowed and denied URLs for reading.": "配置网页读取允许与拒绝的 URL 规则列表。",
    "Configure allowed and denied paths for file reads and writes.": "配置允许和拒绝文件读写的路径规则。",
    "Configure allowed commands outside the sandbox.": "配置允许在沙盒外直接执行的命令白名单。",
    "Configure allowed terminal commands.": "配置允许自动执行的终端命令列表。",
    "Configure editor-specific behaviors and shortcuts.": "配置代码编辑器专属行为偏好与快捷键绑定。",
    "Configure external tools via Model Context Protocol.": "通过模型上下文协议 (MCP) 配置与接入外部扩展工具。",
    "Configure hooks that run on agent lifecycle events.": "配置在 Agent 生命周期特定事件发生时触发的 Hook 钩子。",
    "Configure tab completion, suggestions, and navigation behavior.": "配置 Tab 键补全、智能建议以及快速导航交互行为。",
    "Configure the agent's visual theme and display preferences.": "配置 Agent 的视觉主题风格与界面显示首选项。",
    "Configure the default width of markdown artifacts.": "设置 Markdown 工件预览面板的默认显示宽度。",
    "Configure the default width of tables.": "设置数据表格在界面中的默认呈现宽度。",
    "Configure the maximum width of the conversation panel.": "设置主会话面板的最大显示宽度限制。",
    "Configure when follow-up messages are sent.": "配置后续跟进消息的自动发送触发时机。",
    "Configure workspace-specific permissions, resources, and customizations.": "配置当前工作区专属的权限、资源映射与自定义扩展。",
    "Configures how the agent tries to access files outside of its working folders.": "配置 Agent 尝试访问其工作目录外文件时的安全策略。",
    "Continue your work from another device with Remote Control. Scan the QR code or open the link below.": "使用远程控制在其他设备上无缝继续工作。请扫描二维码或打开下方链接。",
    "Controls the actions the agent can take.": "控制 Agent 能够执行的操作行为与授权范围。",
    "Controls whether terminal commands require your approval before running.": "控制终端命令在执行前是否需要获得您的人工确认批准。",
    "Controls whether the agent can run custom JavaScript to automate complex browser actions.": "控制 Agent 是否可以运行自定义 JavaScript 脚本以自动化复杂的浏览器交互。",
    "Custom path for the browser user profile directory. Leave empty for default (~/.gemini/antigravity-browser-profile).": "浏览器用户配置目录的自定义路径。留空则使用默认路径 (~/.gemini/antigravity-browser-profile)。",
    "Determines the markup language of the output.": "决定生成输出所使用的标记语言格式。",
    "Developer-only tools. These settings are stored locally in this browser and do not affect other users.": "仅限开发者调试工具。这些设置仅保存在本地客户端，不会影响其他用户。",
    "Display and preserve intermediate thinking steps.": "在对话界面中展示并保留模型的中间深度思考推理过程。",
    "Drag to resize the gutter; double-click to fit it automatically": "拖动以调整边栏大小；双击可自动自适应内容宽度",
    "Every step packed into a lane per kind — no rows, no scrolling": "所有步骤按类型紧凑排入专属泳道 —— 无冗余行，无需横向滚动",
    "Every terminal command requires approval.": "所有终端命令均须获得您的人工批准方可执行。",
    "External tools the agent can call via Model Context Protocol.": "Agent 可通过模型上下文协议 (MCP) 调用的外部工具集合。",
    "Folders the automation agents can access.": "自动化 Agent 被授权访问的文件夹目录列表。",
    "GCP Project ID for enterprise features.": "用于解锁企业级特性的 GCP 项目 ID。",
    "Give the agent awareness of lint errors created by its edits so it can fix them without explicit prompting.": "让 Agent 能实时感知其代码修改引发的语法和代码检查错误，无需用户提示即可自动修正。",
    "Highlight newly inserted text after accepting a Tab completion.": "在接受 Tab 键补全后，对新插入的代码文本进行高亮突出显示。",
    "Hook will only trigger if the tool name matches run_command or view_file.": "Hook 仅在工具名称匹配 run_command 或 view_file 时触发。",
    "Hook will only trigger if the tool name matches run_command.": "Hook 仅在工具名称精确匹配 run_command 时触发。",
    "Hook will only trigger if the tool name starts with browser_.": "Hook 仅在工具名称以 browser_ 开头时触发。",
    "Hook will trigger if any tool is executed.": "任何工具被调用执行时均会触发该 Hook。",
    "I prefer an immediate single response to prioritize productivity right now.": "我希望立即获得单次回答，优先保障当前的生产力与流转效率。",
    "Include default customizations, such as default skills.": "包含官方默认的自定义扩展配置（例如内置的默认 Skills）。",
    "Keep the app accessible from the menu bar and running in the background when all windows are closed.": "当所有窗口关闭时，依然在系统托盘/菜单栏中常驻并在后台保持运行。",
    "Keyboard shortcuts for quick navigation and control.": "用于快速界面导航与精准控制的全局快捷键配置。",
    "Let the agent access past conversations to inform its responses.": "允许 Agent 检索并参考过去的会话记录，以提供更具上下文连续性的回答。",
    "Manage fine-grained permissions for GitHub.": "管理面向 GitHub 的细粒度权限与授权范围。",
    "Manage your conversations from the companion website.": "在配套 Web 网站中管理并查看您的所有历史会话。",
    "Manage your model quota and credits.": "管理您的模型使用配额、额度余量与计费账单。",
    "Manage your notification preferences.": "管理系统通知与消息弹窗的推送首选项。",
    "Manage your plan, credentials, and general preferences.": "管理您的订阅计划、认证凭据以及通用配置选项。",
    "Modify permissions for file, terminal, and MCP tools.": "调整针对文件系统、终端命令以及 MCP 工具的细化权限。",
    "No model specified for Battle Mode, falling back to use current selected model": "对抗模式未指定模型，自动回退使用当前已选定的模型",
    "One row per step, in order — scroll to move through the run": "按执行顺序每步占一行 —— 滚动可完整浏览整个运行过程",
    "Open Agent panel on window reload": "窗口重新加载时自动展开 Agent 面板",
    "Open files in the background if Agent creates or edits them": "当 Agent 创建或编辑文件时，自动在后台静默打开",
    "Open files in the background if the agent creates or edits them": "当 Agent 创建或编辑文件时，自动在后台静默打开",
    "Open the agent panel on window reload": "窗口重载后自动呼出 Agent 侧边面板",
    "Opens in the in-app preview pane. Some sites don't support iframe embedding and may not load.": "在应用内预览窗格中打开。部分网站不支持 iframe 嵌入，可能无法直接加载。",
    "Path to the Chrome/Chromium executable. Leave empty for auto-detection.": "Chrome/Chromium 可执行程序路径。留空则由系统自动探测。",
    "Paths the agent can modify inside this workspace.": "Agent 在当前工作区内被允许修改的文件路径规则。",
    "Paths the agent can modify.": "Agent 被允许直接修改的文件路径规则列表。",
    "Paths the agent can read inside this workspace.": "Agent 在当前工作区内被允许读取的文件路径规则。",
    "Paths the agent can read.": "Agent 被允许读取的文件路径规则列表。",
    "Play a sound when the agent finishes generating a response.": "当 Agent 完成响应生成时播放提示音效。",
    "Port number for Chrome DevTools Protocol remote debugging. Leave empty for default (9222).": "用于 Chrome 开发者工具协议远程调试的端口号。留空使用默认端口 (9222)。",
    "Predict the location of your next edit and navigate you there with a tab keypress.": "智能预测您下一次代码编辑的位置，并支持按 Tab 键一键精准跳转。",
    "Prevent the computer from sleeping while the app is running.": "在 Antigravity 运行期间阻止计算机自动进入系统休眠。",
    "Quickly add and update imports with a tab keypress.": "支持按下 Tab 键快速自动添加与更新模块导入语句。",
    "Replace the default browser right-click menu with quick actions.": "使用专为编程定制的快捷操作菜单替换系统默认的浏览器右键菜单。",
    "Restricts agent tools to a secure, isolated local sandbox.": "将 Agent 的工具调用严格限制在安全、隔离的本地沙盒环境中。",
    "Run in a new worktree": "在新建的独立 Git 工作树中运行",
    "Run in your current workspace": "在当前所在工作区中直接运行",
    "Run terminal commands with sandbox restrictions.": "在沙盒安全限制下受控运行终端命令。",
    "Select the workspace type that will be used for new conversations started with the New Workspace option.": "选择点击“新建工作区”发起新会话时所使用的默认工作区类型。",
    "Set the speed of tab suggestions": "设置 Tab 补全代码建议的响应弹出速度",
    "Show browser notifications when your action is needed or execution finishes.": "当需要您进行人工决策或任务执行完毕时发送系统桌面通知。",
    "Show suggestions when typing in the editor": "在代码编辑器中键入时实时呈现智能补全建议",
    "Simulate a different host (Electron, desktop or mobile Web, Extension, remote control, or installed PWA).": "模拟不同的宿主运行环境（桌面端 Electron、网页版、IDE 扩展、远程控制或 PWA 应用）。",
    "Simulate a different user cohort (Google, External, Enterprise).": "模拟不同类型的用户群体（内部用户、外部个人用户、企业用户）。",
    "Simulate running on a different OS.": "模拟在不同操作系统（Windows、macOS、Linux）环境下的运行表现。",
    "Specifies the agent's behavior when asking for review on artifacts, which are documents it creates to enable a richer conversation experience.": "配置 Agent 在生成工件文档请求您审查时的交互行为策略。",
    "Team of subagents to do long running work": "调度由多个子代理构成的协同集群以处理长时间运行的大型复杂工程任务",
    "Terminal commands the agent can execute in this workspace.": "Agent 在当前工作区中被允许执行的终端命令规则。",
    "Terminal commands the agent can execute.": "Agent 被允许执行的终端命令规则列表。",
    "The agent asks for permission before executing commands matched by a deny list entry.": "当命中了黑名单列表中的指令时，Agent 会强制暂停并请求您的显式授权。",
    "The agent auto-executes commands matched by an allow list entry.": "当命中了白名单列表中的指令时，Agent 将自动批准并立即执行该命令。",
    "This prompt is straightforward and does not need alternative comparisons.": "该提示词意图非常明确，无需在多个备选方案之间进行对抗比对。",
    "This request is not well-suited for parallel Best-of-N generation.": "此任务请求不适合进行并行的 Best-of-N 多方案并发对比。",
    "URLs the agent can actuate on in this workspace.": "Agent 在当前工作区内可通过浏览器进行点击操作的 URL 规则。",
    "URLs the agent can actuate on using the browser.": "Agent 可在浏览器中执行交互操作的 URL 规则列表。",
    "URLs the agent can read or open in the browser.": "Agent 可在浏览器中读取内容或直接打开的 URL 规则列表。",
    "URLs the agent can read or open in this workspace.": "Agent 在当前工作区内被允许读取或打开的 URL 规则列表。",
    "When enabled, 'Explain and Fix' actions will continue in the current conversation instead of starting a new one.": "启用后，“解释并修复”操作将在当前会话中继续跟进，而不会开启全新会话。",
    "When enabled, Agent is given awareness of lint errors created by its edits and may fix them without explicit user prompting.": "启用后，Agent 会自主识别由其代码修改引发的代码检查错误并主动自愈，无需用户额外催促。",
    "When enabled, Agent will use IDE's shell integration to detect and report terminal command execution.": "启用后，Agent 将深度利用 IDE 的 Shell 集成机制精准捕获与上报终端命令运行状态。",
    "When enabled, Antigravity will play a sound when Agent finishes generating a response.": "启用后，当 Agent 完成长篇内容生成时将播放提示音效。",
    "When enabled, sandboxed commands are allowed to make network requests.": "启用后，沙盒内运行的命令将被允许发起外部网络连接请求。",
    "When enabled, the Changes Overview toolbar will automatically expand when Agent finishes generating a response.": "启用后，当 Agent 回复生成完成时，“变更概览”浮动工具栏将自动展开供您快速审查。",
    "When enabled, the agent will be able to access past conversations to inform its responses.": "启用后，Agent 将获得对过去所有历史对话的索引与检索能力，带来更贴心的记忆延续感。",
    "When enabled, the agent will include default customizations, including default skills.": "启用后，Agent 将自动载入并激活官方预设的全部默认自定义技能 (Skills)。",
    "Whether the agent asks you to review its documents.": "配置 Agent 是否在生成设计文档或计划工件时主动提请您人工审阅。",
    "Work with local agents from another device.": "在另一台设备（如手机或平板）上远程连接并操控本地运行的 Agent。"
}

def main():
    repo_root = Path(__file__).resolve().parent.parent
    res_dir = repo_root / "resources"
    cn_file = res_dir / "antigravity-zh-CN.json"
    tw_file = res_dir / "antigravity-zh-TW.json"
    hk_file = res_dir / "antigravity-zh-HK.json"

    # 1. Load existing dictionary
    with open(cn_file, "r", encoding="utf-8") as f:
        full_dict = json.load(f)

    # 2. Merge with settings translations
    full_dict.update(SETTINGS_TRANSLATIONS)

    # Clean up non-words
    clean_dict = {}
    for k, v in full_dict.items():
        k_str = k.strip()
        if not k_str or k_str.startswith(")){") or k_str in ["9222", "all", "\\angl", "\\fbox", "\u2212"]:
            continue
        clean_dict[k_str] = v

    # Sort
    sorted_cn = {k: clean_dict[k] for k in sorted(clean_dict.keys())}

    # Traditional Chinese
    from translate_dictionary import to_traditional
    sorted_tw = {k: to_traditional(v) for k, v in sorted_cn.items()}
    sorted_hk = {k: to_traditional(v) for k, v in sorted_cn.items()}

    with open(cn_file, "w", encoding="utf-8") as f:
        json.dump(sorted_cn, f, ensure_ascii=False, indent=2)

    with open(tw_file, "w", encoding="utf-8") as f:
        json.dump(sorted_tw, f, ensure_ascii=False, indent=2)

    with open(hk_file, "w", encoding="utf-8") as f:
        json.dump(sorted_hk, f, ensure_ascii=False, indent=2)

    print(f"Updated dictionary with all Settings strings: {len(sorted_cn)} terms.")

if __name__ == "__main__":
    main()
