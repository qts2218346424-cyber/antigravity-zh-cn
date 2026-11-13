# 材质包（皮肤）系统使用与制作指南

材质包可以一次性改变 Antigravity 的 **配色、背景图（整窗 / 编辑区 / 侧边栏…，可调透明度与模糊）、字体、图标、桌宠外观**，并支持在任意材质包之上叠加你自己的个性化覆盖层。

- 适用范围：
  - **Agent 桌面端**（`app.asar`，本项目汉化补丁所修改的程序）：切换材质包后**实时生效**，无需重启；
  - **Antigravity IDE 编辑器**（基于 VS Code 的工作台）：写入工作台样式并自动修正 `product.json` 校验和，切换后执行“重新加载窗口”即可；
  - **独立桌面桌宠**（Windows）：启动时自动套用当前材质包的桌宠外观。
- **官方更新不会丢失**：所有材质包、当前选择与个人设置都保存在用户配置目录，而不是 Antigravity 安装目录；开启“自动维护”后，官方更新覆盖补丁时会自动重新注入。

---

## 目录

- [快速上手](#快速上手)
- [文件存放位置](#文件存放位置)
- [skin.json 清单格式](#skinjson-清单格式)
- [制作一个材质包（5 分钟）](#制作一个材质包5-分钟)
- [个人覆盖层：在别人的包上微调](#个人覆盖层在别人的包上微调)
- [命令行速查](#命令行速查)
- [更新后自动重新注入](#更新后自动重新注入)
- [卸载与还原](#卸载与还原)
- [实现原理](#实现原理)
- [常见问题](#常见问题)

---

## 快速上手

### 方式一：图形界面（推荐）

- 下载打包好的 `AntigravityZhCN.exe`（GitHub Actions →「构建一体化管理器」→ 构建产物），双击运行；
- 或在源码目录双击 `材质包与汉化管理器.bat`（需要 Python 3.10+）。

界面包含 5 个页签：

| 页签 | 功能 |
| :--- | :--- |
| 材质包 | 列表 + 预览图，**双击或点“一键应用”切换**；导入 / 导出 `.zip`；复制为新包；删除 |
| 自定义 | 配色、背景图（位置 / 透明度 / 模糊 / 缩放）、字体、图标滤镜、桌宠外观、追加 CSS；可作用于当前包或全局 |
| 汉化补丁 | 安装 / 重新应用汉化、还原官方原版、禁止 / 恢复官方自动更新 |
| 桌宠 | 启动独立桌面桌宠（Windows） |
| 自动维护 | 开机后台检测 Antigravity 更新并自动重新注入 |

> 第一次使用：先在「汉化补丁」页点一次 **安装 / 重新应用汉化**（会注入材质包加载器），之后切换材质包都是实时生效的。

### 方式二：命令行

```bash
python scripts/agzh.py skin list               # 列出材质包（* 为当前使用）
python scripts/agzh.py skin use sakura-light   # 切换
python scripts/agzh.py skin off                # 关闭皮肤
```

### 内置示例材质包

| id | 名称 | 说明 |
| :--- | :--- | :--- |
| `midnight-dark` | 午夜深空 · 暗色 | 深蓝暗色 + 极淡星空整窗背景，代码字体 Cascadia Code，桌宠小王子 |
| `sakura-light` | 樱花 · 浅色 | 樱花粉浅色，编辑区半透明樱花背景，示范 codicon 图标替换与自定义 CSS |
| `nezuko-bamboo` | 祢豆子 · 竹筒与麻叶 | 粉 / 墨红配色，侧边栏麻叶纹平铺 + 窗口竹篓剪影，图标色相偏移，桌宠固定祢豆子 |

---

## 文件存放位置

| 系统 | 配置目录 |
| :--- | :--- |
| Windows | `%APPDATA%\antigravity-zh-cn\` |
| macOS | `~/Library/Application Support/antigravity-zh-cn/` |
| Linux | `$XDG_CONFIG_HOME/antigravity-zh-cn/`（默认 `~/.config/antigravity-zh-cn/`） |

可用环境变量 `AGZH_CONFIG_DIR` 改为任意目录（便携模式）。目录结构：

```text
antigravity-zh-cn/
├─ skins/<id>/skin.json        # 已安装的材质包（内置包首次运行时自动复制进来）
├─ overrides/_global.json      # 全局个人覆盖层（作用于所有材质包）
├─ overrides/<id>.json         # 针对某个材质包的个人覆盖层
├─ overrides/assets/           # 在界面里选择的图片 / 字体会被复制到这里
├─ compiled/active-skin.json   # 编译后的运行时载荷（Agent 主进程实时监听此文件）
├─ compiled/active-skin.css    # 同一份样式，便于调试
├─ state.json                  # 当前材质包、自动维护开关、上次补丁参数与文件指纹
└─ logs/auto-reapply.log       # 自动重注入日志
```

---

## skin.json 清单格式

一个材质包就是一个文件夹（或其 `.zip`），根部有 `skin.json`，其余图片 / 字体 / CSS 用**相对路径**引用。

```jsonc
{
  "schema": 1,                       // 清单版本，目前固定为 1
  "id": "my-skin",                   // 必填：小写字母/数字/._-，与文件夹名一致
  "name": "我的皮肤",                 // 必填：显示名称
  "version": "1.0.0",                // 必填
  "author": "你的名字",
  "description": "一句话介绍",
  "base": "dark",                    // dark | light
  "preview": "preview.png",          // 预览图（界面列表展示，建议 360×220 PNG）

  "colors": {                        // 语义化配色（任选，CSS 颜色：#rgb/#rrggbb/#rrggbbaa/rgb()/hsl()/颜色名）
    "background": "#1a0e14",         // 编辑器背景
    "foreground": "#f6e3ea",         // 主文字
    "accent": "#f06292",             // 强调色（按钮、焦点框、徽标、链接、进度条）
    "accentForeground": "#1a0e14",
    "sidebar": "#24111b", "activityBar": "#160a10", "titleBar": "#160a10",
    "statusBar": "#8e1d47", "panel": "#1e0f17", "border": "#4a1f33",
    "selection": "#f0629255", "input": "#2a1520", "muted": "#b98aa0"
  },

  "variables": {                     // 任意 CSS 变量（高级），例如精确覆盖某个 VS Code 主题色
    "--vscode-editorCursor-foreground": "#ff4081"
  },

  "selectors": {                     // 可选：自定义背景挂载点对应的选择器
    "chat": "main"
  },

  "background": [                    // 一个对象或对象数组（可同时给多个区域加背景）
    {
      "image": "bg.webp",            // png / jpg / webp / gif / svg，单个文件 ≤ 8 MB
      "target": "window",            // window | editor | sidebar | panel | terminal | chat
      "opacity": 0.15,               // 0 ~ 1
      "blur": 4,                     // 0 ~ 100 (px)
      "position": "right bottom",    // CSS background-position
      "size": "cover",               // cover | contain | auto | 160px …
      "repeat": "no-repeat",         // no-repeat | repeat | repeat-x | repeat-y | round | space
      "blend": "normal"              // 可选：normal | multiply | screen | overlay | soft-light …
    }
  ],

  "font": {
    "family": "HarmonyOS Sans SC, Microsoft YaHei UI, sans-serif",   // 界面字体
    "size": 13,                                                      // 界面字号 8~40
    "monoFamily": "Sarasa Mono SC, Cascadia Code, monospace",        // 代码 / 终端字体
    "monoSize": 14,
    "ligatures": true,                                               // 连字
    "file": "fonts/MyFont.woff2"     // 可选：随包携带字体（仅 Agent 桌面端生效，IDE 请安装到系统）
  },

  "icons": {
    "filter": "hue-rotate(300deg) saturate(1.3)",   // 对所有 codicon 图标套滤镜
    "color": "#c2185b",                              // 统一图标颜色
    "codicons": {                                    // 按 codicon 名称替换为图片
      "heart": "icons/sakura.svg"
    },
    "selectors": {                                   // 按任意 CSS 选择器替换背景图标（高级）
      ".some-button .icon": "icons/btn.png"
    }
  },

  "css": "/* 任意追加 CSS，最后注入、优先级最高 */",
  "cssFile": "extra.css",            // 或者放到单独文件

  "pet": {                           // 桌宠外观（不修改桌宠动作代码）
    "character": "nezuko",           // nezuko | prince | auto（切换到本包时自动选中一次）
    "sprite": "pet.png",             // 可选：用一张图片替换整个角色形象（透明 PNG/WebP 最佳）
    "filter": "hue-rotate(180deg)",  // 对角色套滤镜（换色）
    "accent": "#f06292",             // 桌宠面板 / 胶囊栏强调色（默认继承 colors.accent）
    "scale": 1.1,                    // 切换到本包时的默认缩放 0.3 ~ 3（之后可在桌宠面板手动调整）
    "hidden": false,                 // true = 隐藏 Agent 窗口内桌宠
    "css": "#nezuko-main-card{border-radius:18px}"
  }
}
```

### 校验规则（导入 / 切换前都会检查）

- `id` / `name` / `version` 必填；`id` 只能用小写字母、数字、`.`、`_`、`-`；
- 所有资源必须是包内相对路径，**禁止绝对路径与 `..`**，扩展名受限，单文件 ≤ 8 MB；
- 颜色、滤镜、字体名、变量值不能含 `; { } < > \` 等可能“逃逸”出声明的字符；
- `.zip` 导入时防 zip-slip，解压总量 ≤ 64 MB、文件数 ≤ 500，**校验通过后才会落盘**；
- 校验失败会给出逐条中文错误，例如 `background[0].opacity: 必须是 0~1 之间的数字`。

自查命令：`python scripts/agzh.py skin validate 你的包目录或.zip`

---

## 制作一个材质包（5 分钟）

1. **以现有包为模板**：界面「材质包 → 复制为新包」，或
   ```bash
   python scripts/agzh.py skin new sakura-light my-skin "我的皮肤"
   ```
   新包出现在 `配置目录/skins/my-skin/`。
2. **改 `skin.json`**：换配色、把背景图放进文件夹并改 `background.image`。
3. **生成预览图**（可选，需要 Pillow）：
   ```bash
   python scripts/build_skin_assets.py --preview --dir "<配置目录>/skins/my-skin"
   ```
4. **启用**：`python scripts/agzh.py skin use my-skin`（或界面双击）。
5. **分享**：界面「导出 .zip」，或 `python scripts/agzh.py skin export my-skin ./`。对方用「导入 .zip」即可。

小技巧：

- 背景图透明度一般 `0.06 ~ 0.25` 最舒服，太高会影响阅读；整窗背景建议配合 `blur`；
- 想精确改某个界面颜色时，用 `variables` 覆盖对应的 `--vscode-*` 变量（IDE 中可用“开发人员: 检查编辑器标记 / 切换开发人员工具”查看变量名）；
- Agent 桌面端的部分区域如果没被默认规则覆盖，可在 `css` 中用开发者工具（汉化补丁已开启 DevTools）查到的选择器补充。

---

## 个人覆盖层：在别人的包上微调

覆盖层与材质包格式相同，但**所有字段都是可选的**，合并顺序：

```text
材质包 skin.json  ←  overrides/_global.json（全局）  ←  overrides/<id>.json（单包）
```

合并规则：

- 对象逐键深度合并；写 `null` 表示删除该键（恢复为不设置）；
- `background` 若材质包是数组、覆盖层给一个对象 → **只调整第一张（主背景）**；覆盖层给数组 → 按下标逐项合并，某项写 `null` 删除该背景；
- `css` **追加**在材质包 CSS 之后（不是替换）。

界面「自定义」页保存的就是覆盖层；勾选“作为全局设置”则写入全局层。命令行：

```bash
python scripts/agzh.py skin override set background.opacity 0.25
python scripts/agzh.py skin override set colors.accent '"#ff8800"'      # 值按 JSON 解析
python scripts/agzh.py skin override asset pet.sprite ~/Pictures/my-pet.png
python scripts/agzh.py skin override set font.size 14 --global
python scripts/agzh.py skin override show
python scripts/agzh.py skin override reset
```

导出材质包时默认会把**单包覆盖层**烘焙进导出的 `skin.json`（含引用的图片），方便把你的调整分享给别人；加 `--no-override` 可只导出原包。

---

## 命令行速查

```bash
python scripts/agzh.py status                         # 总体状态
python scripts/agzh.py skin list | current | off
python scripts/agzh.py skin use <id> [--no-ide] [--ide-dir 路径]
python scripts/agzh.py skin import 包.zip [--overwrite] [--use]
python scripts/agzh.py skin export <id> 目标目录或.zip [--no-override]
python scripts/agzh.py skin new <模板id> <新id> <名称>
python scripts/agzh.py skin remove <id>
python scripts/agzh.py skin validate 目录或.zip
python scripts/agzh.py skin sync-builtin [--force]

python scripts/agzh.py ide status | apply | remove [--dir IDE安装目录]

python scripts/agzh.py l10n install [--lang zh-CN] [--character nezuko] [--no-pet] [--no-skin] [--dir 安装目录]
python scripts/agzh.py l10n restore [--keep-ide]

python scripts/agzh.py reapply status | enable | disable
python scripts/agzh.py reapply check [--apply] [--force-running]
python scripts/agzh.py reapply watch [--interval 120]

python scripts/agzh.py pet launch
```

打包版可用 `AntigravityZhCN.exe cli <同上参数>`（Windows 下为图形程序，命令行输出不可见，适合脚本调用）。

原有 `scripts/patch_antigravity.py install` 默认也会注入材质包加载器，可加 `--no-skin` 关闭。

---

## 更新后自动重新注入

在界面「自动维护」勾选，或 `python scripts/agzh.py reapply enable`：

| 系统 | 方式（均为当前用户级，无需管理员） |
| :--- | :--- |
| Windows | `HKCU\Software\Microsoft\Windows\CurrentVersion\Run\AntigravityZhCnAutoReapply` → 开机启动 `AntigravityZhCN.exe --background`（源码版为 `pythonw app\agzh_app.py --background`） |
| macOS | `~/Library/LaunchAgents/com.antigravity-zh-cn.autoreapply.plist`，登录时及每 10 分钟执行一次 `--check-once` |
| Linux | `~/.config/autostart/antigravity-zh-cn-autoreapply.desktop` |

检测逻辑：

1. 每次打补丁成功后，在 `state.json` 记录补丁参数（语言、启动动画角色、是否桌宠 / 皮肤）与 `app.asar` 指纹（大小、修改时间、sha256）；
2. 后台每 2 分钟只做一次 `stat`；指纹变化时才读取文件确认补丁标记是否还在；
3. 标记丢失 = 被官方更新覆盖 → **等 Antigravity 退出后**（不会强杀正在使用的程序）用原参数自动重打，并刷新新版本的 `app.asar.bak` 备份；macOS 会自动 ad-hoc 重签名；
4. IDE 工作台样式块丢失或与当前皮肤不一致时自动重新写入并修正校验和；
5. 你主动「还原官方原版」后会被记录，**不会再被自动打回去**；重新安装汉化即可恢复自动维护。

日志：`配置目录/logs/auto-reapply.log`。

> 与 `scripts/setup_watchdog.bat` / `auto_maintainer.py` 的区别：那是**维护者**用的流水线（抓词条、翻译、跑测试、`git push`）；这里是面向**普通用户**的轻量重注入，不碰 Git。

---

## 卸载与还原

| 想做的事 | 操作 |
| :--- | :--- |
| 暂时关闭皮肤 | `skin off` 或界面「关闭皮肤」（Agent 端立即移除样式，IDE 样式块被剥离） |
| 只撤销 IDE 修改 | `python scripts/agzh.py ide remove`：剥离样式块、恢复与官方完全一致的文件和校验和 |
| 完全还原 | 界面「还原官方原版」或 `l10n restore`：恢复 `app.asar.bak`、剥离 IDE 样式、停止自动重打 |
| 关闭开机自启 | `reapply disable` 或取消勾选「自动维护」 |
| 清除所有数据 | 删除上表中的配置目录 |

所有注入均可重复执行（幂等）：Agent 端总是基于纯净备份重新打补丁；IDE 端先剥离旧样式块再写入，不会越叠越多。

---

## 实现原理

```text
                 ┌──────────── 用户配置目录（官方更新不会动） ─────────────┐
 skin.json ──┐   │ skins/  overrides/  state.json                           │
 覆盖层   ───┼──▶│ 编译 → compiled/active-skin.json (CSS + 桌宠参数 + 哈希) │
             │   └──────────────┬──────────────────────────────┬──────────┘
             │                  │ fs.watchFile 实时监听          │ 写入样式块 + 修正 checksums
             ▼                  ▼                                ▼
   agzh_app / agzh.py   Agent 桌面端 dist/utils.js        IDE workbench.desktop.main.css
                        主进程皮肤加载器：                 /* __AGZH_SKIN_BEGIN__ hash=… */
                        insertCSS / removeInsertedCSS      …                      
                        + 渲染层 skin-runtime.js(桌宠)     /* __AGZH_SKIN_END__ */
```

- **Agent 桌面端**：补丁在 `dist/utils.js` 的主进程钩子中加入 `__agzhSkin` 加载器，在 `dom-ready` / `did-finish-load` / 内嵌 webview 时调用 `webContents.insertCSS`；切换材质包只是改写 `compiled/active-skin.json`，加载器监听到变化后先 `removeInsertedCSS` 再注入新样式 —— **无需重新打补丁、无需重启**。
- **背景图**使用 `::before / ::after` 伪元素覆盖层（`pointer-events: none`），不需要把界面各层改透明，兼容性最好；图片以 data URI 内嵌，不依赖 `file://` 访问权限。
- **桌宠**：`resources/skin-runtime.js` 只通过 CSS 覆盖和外层叠加节点改变外观（滤镜、强调色、替换形象图、默认角色 / 缩放），**不修改 `nezuko-pet.js` 的动作代码**；独立桌面桌宠窗口在加载完成后通过 `evaluate_js` 注入同一段运行时。
- **IDE 校验和**：VS Code 架构会对 `product.json` 中 `checksums` 列出的文件做 sha256 校验，不一致时提示“安装似乎已损坏”。写入样式后同步计算 `base64(sha256)`（去掉尾部 `=`）更新对应项；还原时一并恢复。

---

## 常见问题

**Q：切换后 Agent 桌面端没变化？**
确认已用新版补丁安装过一次汉化（「汉化补丁 → 安装 / 重新应用」，不要勾掉“注入材质包加载器”）；旧版补丁没有加载器。

**Q：IDE 没变化 / 没找到 IDE？**
IDE 需要「开发人员: 重新加载窗口」或重启。若安装在非默认位置，用 `python scripts/agzh.py ide apply --dir "IDE 安装目录"`（会记住该路径）。macOS 修改 `.app` 内文件后如提示已损坏，请执行 `codesign --force --deep -s - /Applications/Antigravity.app`。

**Q：IDE 写入时报权限错误？**
IDE 装在 `Program Files` 等受保护目录时需要以管理员身份运行管理器一次。

**Q：会不会影响代码、终端或输入内容？**
不会。材质包只注入样式与桌宠外观层；背景覆盖层不接收鼠标事件。

**Q：自制包里的某张背景只想在 IDE 生效？**
目前同一份 CSS 同时用于两端；可以用 `selectors` 把该背景挂到只存在于 IDE 的选择器（如 `.monaco-workbench .part.editor > .content`，这也是 `editor` 的默认值）。
