<div align="center">

# Antigravity Studio

**基于 Tauri v2 + React 19 + Rust 构建的新一代 Antigravity 全能中文控制中心与美学引擎**

[![构建与 OTA 发布](https://github.com/qts2218346424-cyber/antigravity-zh-cn/actions/workflows/release.yml/badge.svg)](https://github.com/qts2218346424-cyber/antigravity-zh-cn/actions/workflows/release.yml)
[![最新版本](https://img.shields.io/github/v/release/qts2218346424-cyber/antigravity-zh-cn?label=Latest%20Release&color=6366f1)](https://github.com/qts2218346424-cyber/antigravity-zh-cn/releases)
[![技术栈](https://img.shields.io/badge/Tauri%20v2-React%2019%20%2B%20Rust-0ea5e9.svg)](src-tauri/tauri.conf.json)
[![License: MIT](https://img.shields.io/badge/License-MIT-emerald.svg)](LICENSE)
![支持平台](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-64748b)

**多账号额度调度 · 本地 API 反代 · 客户端双层汉化 · 高定光学材质引擎 · 独立灵动桌面伴侣 · Minisign OTA 自动推送**

[核心能力矩阵](#-核心能力矩阵) · [高定光学材质包](#-高定光学材质包系统) · [汉化与系统增强](#-全量无损汉化与哨兵守护) · [独立桌面伴侣](#-独立灵动桌面伴侣) · [OTA 发布流水线](#-ota-自动更新与发布流水线) · [本地构建与开发](#-本地开发与编译)

</div>

---

> [!NOTE]
> **原生架构全面重构**：`Antigravity Studio` 彻底告别早期零散批处理与内置脚本注入方式，以高性能原生桌面内核统一集成「多账号配额管理」、「本地反代网关」、「Antigravity 全量汉化注入」、「双端光学材质热重载引擎」与「独立透明桌面伴侣」，并通过 GitHub Releases 签名 OTA 流水线向全平台持续推送更新。

---

## ✨ 核心能力矩阵

| 功能板块 | 架构设计与关键特性 |
| :--- | :--- |
| 🎨 **高定光学材质引擎** | 内置 10 款精选主题（含《CLANNAD》四重奏皮肤）与 `surfaces` 物理表面参数编译器（圆角 `radius`、磨玻璃模糊 `glass_blur`、卡片通透度 `card_opacity`、边缘辉光 `border_glow`、胶片噪点 `noise_grain` 与阴影景深 `shadow_elevation`），支持画廊微缩 IDE 实时预览与 **Color DNA** 在线调色实验室。 |
| ⚡ **双端同步无损注入** | 主程序 (`Antigravity` 客户端) 通过 `BaseWindow + WebContentsView` 全子视图监听器与实时 CSS 变量引擎驱动热重载；`Antigravity IDE` 同步编译至 `workbench.desktop.main.css` 与 `jetskiMain.tailwind.css`，彻底免除主进程 `FSWatcher EPERM` 崩溃与旧补丁污染。 |
| 🈶 **全量双层汉化系统** | 原生 Rust 实现 `app.asar` 无损解包与 SHA-256 Integrity 重建，支持 `zh-CN` / `zh-TW` / `zh-HK`，覆盖 Electron 主进程菜单/托盘与渲染层全部 UI；保留官方原版极速启动流程，精确避让代码区、终端与模型正文，并内置 **老版本内置宠物代码 (`__AGY_NEZUKO_PET_INITIALIZED__`) 自动侦测与剥离清理**。 |
| 🪐 **独立灵动桌面伴侣** | 从客户端进程完全剥离，运行于独立透明置顶窗口（`index.html?pet=1`），搭载高精零白边多姿态透明原画、2.5D 弹性动力学与 3D 视差效果、灵动岛状态玻璃坞、毫秒级 LRC 二分时间轴黑胶歌词舱、低配额预警及配额舱内一键刷新/切号；内置 **祢豆子（米豆子）、小王子、冈崎汐（团子大家族）、炭治郎、善逸、伊之助** 6 大动漫角色，并支持 **自定义本地 PNG/WebP/GIF/SVG 立绘热导入**。 |
| 🧪 **全链路自检与测试台** | 内置可视化 **全链路测试台 (`DiagnosticsTab`)** 一键巡检后端词典、光学材质编译器、伴侣骨骼缓存、客户端路径探测与本地 API 反代连通性，同时提供伴侣动作/合成音效沙盒演练；工程侧配备零外部依赖 `npm test` 自动化单元测试引擎。 |
| 🛡️ **Tokio 自动维护哨兵** | 后台异步守护线程定时检查官方版本更新及哈希变更，一旦官方更新覆盖了 `app.asar` 或 IDE 样式，待客户端空闲后自动静默重注汉化、Skill 描述与当前激活材质。 |
| 🔑 **账号调度与反代网关** | 原生管理多账号 OAuth / Token 刷新、额度监控、“蹬额度”智能切换调度、Token 用量统计、请求调用监控与本地 HTTP API 代理服务。 |
| 🚀 **OTA 签名自动更新** | 集成 `@tauri-apps/plugin-updater` 与后台更新检测器，基于 `updater.json` 与 Minisign 公私钥数字签名校验，支持应用内一键下载并平滑重启升级。 |

---

## 🎨 高定光学材质包系统

全新的材质系统以「**Color DNA 配色变量 + 物理表面光学参数**」双轮驱动，所有内置主题清单位于 [`resources/skins/`](resources/skins)：

| 主题 ID | 风格定位 | 视觉与光学特征 |
| :--- | :--- | :--- |
| **`obsidian-glass`** | 黑曜石磨玻璃（默认） | 深邃暗曜基底配合 24px 磨玻璃高斯模糊与细腻噪点纹理，夜战编码首选 |
| **`vermilion-lacquer`** | 东方朱漆美学 | 漆器朱红与鎏金对比色板、低饱和通透卡片层与柔和金属高光描边 |
| **`nordic-aurora`** | 北境极光玻璃 | 冷冽极光蓝绿梯度光晕叠加扩散投影，打造克制通透的北欧极简观感 |
| **`nezuko-bamboo`** | 祢豆子竹林和风 | 麻叶织纹视觉基底与绯樱竹翠撞色体系 |
| **`sakura-light`** | 樱雪晴空浅色 | 清透高亮日间色板、矢量樱瓣质感与柔和玻璃边线 |
| **`midnight-dark`** | 午夜星尘深空 | 深空星海高对比阅读色域与专注代码高亮氛围 |
| **`clannad-sakura-hill`** | CLANNAD · 光坂坡道与团子 | 春季奶油樱白浅色基底、樱花缎带状态栏与右下角微笑团子大家族暗纹 |
| **`clannad-illusionary-orbs`** | CLANNAD · 幻想世界光玉 | 深宵苍穹蓝黑基底、奇迹暖金与冰蓝光玉微光、22px 液态亚克力折射 |
| **`clannad-after-sunflower`** | CLANNAD · 汐与晴空花田 | 盛夏麦穗米白护眼底色、向日葵琥珀金高光与澄澈晴空蓝状态栏 |
| **`clannad-starfish-library`** | CLANNAD · 图书室海星与提琴 | 暮色紫檀深空底色、薰衣草提琴弦光与风子纪念木雕海星纹理 |

在工作台 **「汉化与美化 → 光学材质画廊 / Color DNA 实验室」** 中支持：
- **画廊微缩实时渲染**：直观对比各主题色谱条与模拟窗口效果，一键应用至客户端与 IDE；
- **Color DNA 物理调色**：实时调节主题背景/强调色/边框与 6 项表面光学滑块，支持导出/导入 `.zip` 自定义皮肤包。

---

## 🈶 全量无损汉化与哨兵守护

- **客户端一键汉化与备份还原**：自动探测 Antigravity 客户端与 IDE 目录，首次注入前将原始未修补的 `app.asar` 安全保存为 `app.asar.bak`，随时支持无损一键还原官方原版。
- **纯净极速启动**：注入补丁严格聚焦菜单栏、托盘、报错弹窗、DOM 文本正则映射与皮肤热重载钩子，**完全保留官方原生 `dist/loadingOverlay.js` 秒开启动流程**，避免额外遮罩干扰主界面进入。
- **生态附属一键增强**：
  - 批量翻译 `~/.gemini` 下内置及插件 `SKILL.md` 英文描述，自动跳过已有中文项；
  - 一键向 `~/.gemini/GEMINI.md` 写入全中文呈现与深度思考协议；
  - 一键修改或还原官方 `app-update.yml` 自动更新开关，防止汉化补丁被官方静默覆盖。
- **旧版脚本自动清理**：自动扫描客户端 `app.asar` 是否仍残留早期旧脚本嵌入的内置宠物，在状态栏提供一键清扫与重置入口。

---

## 🪐 独立灵动桌面伴侣

桌面伴侣（[`PetWindowView.tsx`](src/components/pet/PetWindowView.tsx)、[`petLogic.ts`](src/components/pet/petLogic.ts) 与 [`PetAndWatchdogTab.tsx`](src/pages/Studio/PetAndWatchdogTab.tsx)）作为完全独立的透明无边框悬浮窗运行，顶栏右侧与系统托盘均内置快捷呼出开关：
- **7 大角色生态与自由立绘定制**：内置 **灶门祢豆子（8 态高精原画与 3D 大正木箱）**、**B612 小王子（颈后双尾 Verlet 物理丝巾与星海玫瑰）**、**冈崎汐 & 团子大家族（八音盒旋律、三色团子叠叠乐与向日葵花田光玉）**、**灶门炭治郎（水之呼吸流体刀纹）**、**我妻善逸（霹雳一闪金雷残影）**、**嘴平伊之助（猪突猛进兽之呼吸）**，并支持一键热导入本地透明 PNG / WebP / GIF / SVG 自定义形象；
- **物理弹簧缓动与防抖解耦拖拽**：采用现代 CSS `linear()` 弹簧曲线（自动适配系统 `prefers-reduced-motion` 无障碍减弱动态设置）与 `5px` 指针位移物理阈值解耦，完美兼顾单击摸头、双击绝技、拖拽拎起与窗口底边任务栏安全锚定；
- **灵动岛、低配额预警与一键切号**：实时监控当前账号主模型算力健康度，低于阈值自动弹出预警气泡，支持在悬浮配额舱内直接刷新额度或一键切换备用账号；
- **声学黑胶与毫秒级 LRC 歌词舱**：搭载 10 组 WebAudio 程序化合成音色，联动本机媒体播放状态，基于二分查找实现多时间标签与 `offset` 校准的毫秒级歌词滚动同步。

---

## 🚀 OTA 自动更新与发布流水线

本仓库通过 GitHub Actions（[`.github/workflows/release.yml`](.github/workflows/release.yml)）全自动完成三端编译、Minisign 签名与 GitHub Releases 分发：

```bash
# 1. 统一递增 package.json / src-tauri/tauri.conf.json / src-tauri/Cargo.toml 版本号
node scripts/bump-version.mjs 5.2.0

# 2. 执行全量自动化单元测试与 TypeScript + Vite 生产打包校验
npm test
npm run build

# 3. 提交并推送版本标签以触发全平台构建与 OTA 制品发布
git add -A
git commit -m "chore: 发布 v5.2.0"
git tag v5.2.0
git push origin main v5.2.0
```

---

## 🛠️ 本地开发与编译

### 环境要求
- **Node.js** `>= 20`
- **Rust** `>= 1.77`（`rustup` / `cargo`）
- **Tauri v2 系统依赖**：Windows 需安装 Visual Studio C++ 构建工具与 WebView2；macOS 需 Xcode Command Line Tools；Linux 需 `libwebkit2gtk-4.1-dev`、`libappindicator3-dev`、`librsvg2-dev`、`patchelf`。

### 常用开发命令

```bash
# 安装前端依赖
npm ci

# 启动 Web 前端纯预览模式（默认 http://localhost:1420）
npm run dev

# 运行全套自动化单元测试（伴侣物理/LRC引擎、路由映射、国际化、配额调度等）
npm test

# 执行 TypeScript 类型校验与 Vite 生产构建
npm run build

# 启动完整 Tauri v2 桌面端开发调试
npm run tauri dev

# 打包当前系统桌面端安装包
npm run tauri build
```

---

## 📂 工程目录结构

```text
antigravity-zh-cn/
├── .github/workflows/
│   └── release.yml                # 多平台 Tauri 自动构建与 OTA 发布流水线
├── resources/
│   ├── skins/                     # 6 款内置高定光学材质主题包（skin.json / 变量 / 纹理）
│   ├── media/                     # 桌面伴侣高清 WebP 分肢与立绘资产
│   ├── antigravity-zh-*.json      # 简/繁体双语界面词典
│   ├── rules-zh-CN.json           # 动态正则汉化规则库
│   ├── desktop-zh-CN.json         # 客户端主进程菜单与托盘汉化字典
│   ├── runtime-zh.js              # 渲染层高性能 DOM 汉化运行时
│   └── skin-runtime.js            # 客户端与全子视图光学皮肤动态注入脚本
├── scripts/
│   └── bump-version.mjs           # 多端版本号一键同步工具
├── src/                           # React 19 + TypeScript + Tailwind 前端源码
│   ├── components/pet/            # 独立透明桌面伴侣窗口视图
│   ├── pages/Studio/              # 汉化与美化控制中心（画廊 / Color DNA / 汉化 / 伴侣与守护）
│   └── services/studioService.ts  # Tauri IPC 调用封装
└── src-tauri/                     # Rust 后端与 Tauri v2 宿主核心
    ├── tauri.conf.json            # 窗口策略、资源映射与 OTA Updater 端点配置
    └── src/modules/studio/        # ASAR 原生解包重封、汉化修补、材质编译与守护哨兵
```

---

<div align="center">

基于 [MIT License](LICENSE) 开源 · **Antigravity Studio**

</div>
