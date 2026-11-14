<div align="center">

# Antigravity Studio

**基于 Tauri v2 + React 19 + Rust 的新一代 Antigravity 全能桌面控制中心**

[![构建与 OTA 发布](https://github.com/qts2218346424-cyber/antigravity-zh-cn/actions/workflows/release.yml/badge.svg)](https://github.com/qts2218346424-cyber/antigravity-zh-cn/actions/workflows/release.yml)
[![最新版本](https://img.shields.io/badge/version-v5.0.3-6366f1.svg)](https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases)
[![技术栈](https://img.shields.io/badge/Tauri%20v2-React%2019%20%2B%20Rust-0ea5e9.svg)](src-tauri/tauri.conf.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
![支持平台](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-64748b)

**多账号与反代网关 · 客户端全量中文化 · 高定光学材质引擎 · 3D 视差灵动桌面伴侣 · 全自动 OTA 签名推送**

[核心矩阵](#-核心能力矩阵) · [光学材质系统](#-高定光学材质包系统) · [桌面伴侣](#-3d-视差灵动桌面伴侣) · [OTA 发布与自动更新](#-ota-自动更新与发布流水线) · [本地构建与开发](#-本地开发与编译)

</div>

---

> [!NOTE]
> **全新架构重构**：本项目已全面告别旧版 Python / 批处理脚本维护模式，基于 `Antigravity-Manager` 原生桌面内核完成深度重塑，将多账号调度、API 本地反代中继、官方客户端中文化注入、高定光学材质引擎与独立透明桌面伴侣原生融合为单一高性能跨平台客户端。

---

## ✨ 核心能力矩阵

| 功能模块 | 架构与核心特性 |
| :--- | :--- |
| 🎨 **高定光学材质引擎** | 内置 6 款精选主题与 `surfaces` 物理光学编译器（控制圆角 `radius`、磨玻璃模糊 `glass_blur`、通透度 `card_opacity`、边缘辉光 `border_glow`、胶片噪点 `noise_grain` 与阴影景深 `shadow_elevation`），支持画廊微缩实时 IDE 预览窗与 Color DNA 实验室实时调色。 |
| 🪐 **3D 视差灵动桌面伴侣** | 独立透明置顶窗口（`index.html?pet=1`），搭载三层景深鼠标 3D 倾斜追踪、底部物理接触投影、体积光晕、矢量 SVG 飘落粒子、Apple 灵动岛玻璃坞、旋转黑胶声学歌词舱及账号算力遥测仪表。 |
| 🈶 **全量双层汉化引擎** | 支持 `zh-CN` / `zh-TW` / `zh-HK`，覆盖 Electron 主进程菜单托盘与渲染层全部 UI，内置静态词典、动态正则规则与 `asar` 备份/一键还原机制，精确排除代码编辑器、终端与对话正文。 |
| 🛡️ **Tokio 自动维护哨兵** | 后台异步守护线程持续监测官方客户端更新或校验和变化，在 `app.asar` 被覆盖后自动重注汉化补丁与光学材质样式。 |
| 🚀 **OTA 在线签名更新** | 集成 `@tauri-apps/plugin-updater` 与 Rust 端更新检测器（`update_checker.rs`），支持客户端内一键检查新版本、校验 Minisign 数字签名、后台下载并无感重启升级。 |
| ⚡ **账号管理与反代中继** | 原生承接多账号配额监控、Token 自动刷新、HTTP/API 反代中继网关及模型路由能力，统一管理 AI 工作流。 |

---

## 🎨 高定光学材质包系统

全新的材质引擎将传统静态配色升级为「Color DNA + 物理表面光学参数」双驱动体系，所有内置主题清单位于 [`resources/skins/`](resources/skins)：

| 主题 ID | 风格定位 | 核心光学特征 |
| :--- | :--- | :--- |
| **`obsidian-glass`** | 黑曜石磨玻璃（默认） | 深邃黑曜基底配合 24px 高强度毛玻璃与细腻噪点纹理，极客夜间首选 |
| **`vermilion-lacquer`** | 东方朱漆美学 | 温润漆器红金对比色板、低饱和卡片通透度与柔和金属高光描边 |
| **`nordic-aurora`** | 北境极光玻璃 | 冷冽深海蓝绿渐变光斑叠加高景深扩散投影，呈现通透北欧极简感 |
| **`nezuko-bamboo`** | 祢豆子竹林和风 | 麻叶纹底图与暖粉朱绯撞色体系，搭配和风动态加载过渡层 |
| **`sakura-light`** | 樱雪晴空浅色 | 清透亮白基底、矢量樱花元素与柔和玻璃高光 |
| **`midnight-dark`** | 午夜星尘深空 | 深空星海暗色域与高对比语法阅读强调色 |

在客户端 **Studio · 光学美化工坊** 中可体验：
- **光学材质画廊**（[`SkinGalleryTab.tsx`](src/pages/Studio/SkinGalleryTab.tsx)）：按风格分类筛选，每张卡片内置微缩 **IDE 实时渲染预览窗** 与 **Color DNA 色谱条**。
- **Color DNA 实验室**（[`CustomizerTab.tsx`](src/pages/Studio/CustomizerTab.tsx)）：支持 3 组核心色彩实时吸管微调、6 项物理表面滑块调节，并在右侧 **1:1 Live Viewport 光学模拟器** 中实时预览对话气泡与 `Thinking Process` 卡片质感。

---

## 🪐 3D 视差灵动桌面伴侣

独立悬浮伴侣窗（[`PetWindowView.tsx`](src/components/pet/PetWindowView.tsx)）与控制中心（[`PetAndWatchdogTab.tsx`](src/pages/Studio/PetAndWatchdogTab.tsx)）共同构成桌面端伴侣生态：

- **三层景深 3D 视差**：实时捕获指针矢量位置，对背景光晕层、主体立绘层与前景粒子层施加差异化 3D 透视旋转（`perspective` / `rotateX` / `rotateY`）与物理接触投影。
- **Apple 灵动岛玻璃坞**：顶部自适应胶囊状态条，集成伴侣状态脉冲灯、工作时长计时、算力额度与快捷操作入口。
- **声学黑胶歌词舱**：内置旋转黑胶唱片动效、双行 LRC 歌词同步渲染及声学主题切换。
- **多生态场景联动**：一键切换不同角色立绘（祢豆子、小王子等）与环境粒子氛围。

---

## 🚀 OTA 自动更新与发布流水线

本仓库已全面配置基于 GitHub Releases 与 Minisign 签名的全自动 OTA 更新推送体系，所有更新检测与下载端点均已定向至 `qts2218346424-cyber/antigravity-zh-cn`：

### 1. 架构链路
- **自动构建工作流**：[`.github/workflows/release.yml`](.github/workflows/release.yml) 在推送 `v*` 标签后自动执行前端校验、构建 Windows / macOS（Universal）/ Linux 安装包，并通过 `tauri-apps/tauri-action@v0` 生成签名制品与 `updater.json` 清单发布至 GitHub Releases。
- **客户端检查与安装**：Rust 后台模块 [`update_checker.rs`](src-tauri/src/modules/update_checker.rs) 与 [`tauri.conf.json`](src-tauri/tauri.conf.json) 中的 `plugins.updater.endpoints` 拉取对应版本清单，由前端 [`UpdateNotification.tsx`](src/components/UpdateNotification.tsx) 提示并自动完成签名校验与覆盖安装。

### 2. 首次部署发布者密钥（重要）
为了确保您向用户推送的 OTA 更新包能够通过本地桌面端的安全签名校验，在首次触发正式发版流水线前，请务必完成以下一次性配置：

1. **生成您的专属签名密钥对**：
   ```bash
   npx tauri signer generate -w ~/.tauri/antigravity-studio.key
   ```
2. **填入公钥到客户端配置**：
   打开 [`src-tauri/tauri.conf.json`](src-tauri/tauri.conf.json)，将生成的公钥字符串（`.key.pub` 内容）替换写入 `plugins.updater.pubkey`。
3. **配置 GitHub 仓库 Secrets**：
   进入仓库 `Settings -> Secrets and variables -> Actions`，新增以下两个机密变量：
   - `TAURI_SIGNING_PRIVATE_KEY`：粘贴上一步生成的私钥全文（`antigravity-studio.key` 内容）
   - `TAURI_SIGNING_PRIVATE_KEY_PASSWORD`：生成密钥时设置的密码（如未设置可留空字符串）
4. **一键升级版本号并推送发布**：
   ```bash
   # 同步更新 package.json、src-tauri/tauri.conf.json、src-tauri/Cargo.toml
   node scripts/bump-version.mjs 5.0.4

   git add .
   git commit -m "chore: 发布 v5.0.4 版本"
   git tag v5.0.4
   git push origin main --tags
   ```
   推送标签后，GitHub Actions 将自动编译三端安装包、签名并更新 `updater.json`，所有已安装客户端即可立即收到新版本更新推送。

---

## 🛠️ 本地开发与编译

### 环境要求
- **Node.js** >= 20
- **Rust** >= 1.77（`rustup` / `cargo`）
- **Tauri v2 系统依赖**：Windows 需安装 Visual Studio C++ 构建工具与 WebView2；macOS 需 Xcode Command Line Tools；Linux 需 `libwebkit2gtk-4.1-dev`、`libappindicator3-dev`、`librsvg2-dev`、`patchelf`。

### 常用命令

```bash
# 1. 安装前端依赖
npm ci

# 2. 仅运行 Web 前端开发预览（默认端口 1420）
npm run dev

# 3. 执行 TypeScript 类型校验与 Vite 生产打包
npm run build

# 4. 启动完整的 Tauri v2 桌面端开发调试模式
npm run tauri dev

# 5. 构建当前平台的正式安装包与 OTA 更新产物
npm run tauri build
```

---

## 📂 工程目录速览

```text
antigravity-zh-cn/
├── .github/workflows/
│   └── release.yml                # 多平台 Tauri 构建与 OTA updater.json 自动发布流水线
├── resources/
│   ├── skins/                     # 6 款内置光学/风格材质包（含 skin.json 与纹理资产）
│   ├── media/                     # 桌宠立绘、启动动画媒体资产
│   ├── splash/                    # 启动画面模板
│   ├── antigravity-zh-*.json      # 简/繁体界面翻译词典
│   ├── rules-zh-CN.json           # 动态正则汉化规则集
│   └── *.js                       # 官方客户端运行时注入脚本（汉化、皮肤、伴侣、加载遮罩）
├── scripts/
│   └── bump-version.mjs           # 多端配置文件版本号一键同步脚本
├── src/                           # React 19 + TypeScript + Tailwind 前端源码
│   ├── components/pet/            # 3D 视差独立透明桌宠窗口视图
│   ├── pages/Studio/              # 光学美化工坊（画廊、Color DNA 实验室、汉化、伴侣、哨兵）
│   └── services/studioService.ts  # Tauri IPC 调用封装与 Web 预览回退数据
└── src-tauri/                     # Rust 后端与 Tauri v2 宿主配置
    ├── tauri.conf.json            # 应用元信息、多窗口定义、资产映射与 OTA Updater 端点
    └── src/modules/               # 账号调度、API 反代、OTA 检测与 Studio 引擎模块
```

---

<div align="center">

基于 [MIT License](LICENSE) 开源 · 用心打造的 Antigravity 桌面生态控制中心

</div>
