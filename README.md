# RainyOCR

<p align="center">
  <img src="images/rainyocr_tray_icon.svg" alt="RainyOCR tray icon" width="128" height="128">
</p>

<p align="center">
  简体中文 · <a href="README_en-US.md">English</a>
</p>

RainyOCR 是一个低打扰的 OCR 翻译工具：框选游戏文本区域后，即可通过按钮或快捷键截图、识别并翻译到独立小窗口中。适用于 Galgame、RPGMaker 等固定文本窗口的游戏，也适用于漫画与同人本等翻译。

<p align="center">
  <img src="images/preview.png" alt="All RainyOCR Windows" width="540" height="360">
</p>

## 功能特性

- **区域框选**：通过遮罩层选择需要识别的屏幕区域。
- **截图 + OCR + 翻译**：对已选区域截图，调用线上大模型完成文字识别与翻译。
- **独立翻译窗口**：翻译结果显示在轻量级 Translation Popup 中，不打断游戏窗口。
- **系统托盘**：Translation 窗口出现后，主窗口会自动收进托盘；可从托盘恢复主窗口、显示翻译窗口、再次触发翻译或退出程序。
- **快捷键**：默认 `Ctrl+Shift+T`，可在 Settings 中修改；同时用于应用内快捷键和全局热键。
- **模型配置界面**：可在 Settings 中配置 OCR / Translate 的模型名称、网关地址与 API Key。
- **翻译字体大小**：可在 Settings 中调整 Translation 结果字体大小，最大 32px。
- **日间 / 夜间主题**：主界面右上角可切换日间和夜间样式。
- **跨平台适配**：主要面向 Windows，同时对 Linux 截图坐标和 macOS 窗口行为做了兼容处理。

## 技术栈

| 模块           | 技术                                   |
| -------------- | -------------------------------------- |
| 语言           | Python 3.13+                           |
| UI             | PySide6 / Qt for Python                |
| 依赖管理       | uv                                     |
| OCR / 翻译请求 | OpenAI-compatible Chat Completions API |
| 全局快捷键     | pynput                                 |
| 图像处理       | Pillow                                 |
| Linux 截图     | grim（可选，Wayland 环境需要）         |

## 安装

### 1. 克隆项目

```bash
git clone https://github.com/OctoberPrayRain/RainyOCR.git
cd RainyOCR
```

### 2. 安装依赖

推荐使用 `uv`：

```bash
uv sync
```

项目要求 Python `>=3.13`。

### 3. 创建本地配置

```bash
cp .env.example .env
```

然后编辑 `.env`，填入自己的模型配置。

> `.env` 用于保存本地 API Key，请不要提交到 GitHub。

## 配置说明

RainyOCR 使用 OpenAI-compatible 接口，因此你可以接入 OpenAI、反代网关或其他兼容 Chat Completions 格式的模型服务。
网关地址既可以填写 Base URL，也可以填写完整的 `/chat/completions` 地址。比如百炼北京地域可以填写 `https://dashscope.aliyuncs.com/compatible-mode/v1`，RainyOCR 会自动请求 `/chat/completions`。

`.env.example` 中的主要配置项如下：

| 配置项                             | 说明                                                           |
| ---------------------------------- | -------------------------------------------------------------- |
| `OpenAI_OCR_Model_Name`          | OCR / 多模态识别使用的模型名称                                 |
| `OpenAI_OCR_Secret_Key`          | OCR 模型 API Key                                               |
| `OpenAI_OCR_Node`                | OCR 模型网关地址 / Base URL，或完整 `/chat/completions` 地址 |
| `OpenAI_Translate_Model_Name`    | 翻译模型名称                                                   |
| `OpenAI_Translate_Secret_Key`    | 翻译模型 API Key                                               |
| `OpenAI_Translate_Node`          | 翻译模型网关地址 / Base URL，或完整 `/chat/completions` 地址 |
| `RainyOCR_Translation_Font_Size` | Translation 窗口结果字体大小，默认 `15`，最大 `32`         |
| `RainyOCR_Capture_Shortcut`      | 截图翻译快捷键，默认 `Ctrl+Shift+T`                          |

你也可以不手动编辑 `.env`，直接在主界面右上角点击齿轮按钮打开 **Settings**，在那里填写模型、网关、API Key、快捷键和字体大小。

## 启动

```bash
uv run python main.py
```

如果你已经手动安装好依赖，也可以运行：

```bash
python main.py
```

## 使用方法

1. 点击 **Select Region**，框选游戏中需要翻译的文本区域。
2. 点击 **Capture + Translate**，或按下快捷键 `Ctrl+Shift+T`。
3. 等待 OCR 与翻译完成。
4. 在 **Translation** 小窗口中查看结果。
5. 如果主窗口被收进托盘，可以从系统托盘菜单恢复主窗口、显示 Translation 窗口、再次翻译或退出程序。

## 界面说明

### 主窗口

- **月亮 / 太阳按钮**：切换日间和夜间主题。
- **齿轮按钮**：打开 Settings。
- **X 按钮**：关闭主窗口；如果托盘可用，会优先收进托盘。
- **Select Region**：重新选择截图区域。
- **Capture + Translate**：立即对已选区域截图并翻译。

### Translation 窗口

- 正在运行时标题会显示 **Translating...**。
- 成功后标题恢复为 **Translation**。
- 失败时标题显示 **Translation Failed**。
- 可通过 Settings 调整翻译结果字体大小。
- Windows / Linux 下使用自定义无边框窗口，并支持拖动；macOS 下会回退到更稳定的原生窗口行为。

### 系统托盘

托盘入口由 `src/UI/tray.py` 管理，默认加载：

```text
images/rainyocr_tray_icon.svg
```

如果图标加载失败，会回退到系统默认图标。托盘菜单包含：

- Show Main Window
- Show Translation
- Settings
- Capture + Translate
- Quit RainyOCR

## 平台注意事项

### Windows

Windows 是当前优先适配平台。主窗口、设置窗口和 Translation 窗口使用自定义圆角样式，并提供右上角关闭按钮与拖动行为。

### macOS

macOS 上 Qt 对透明无边框窗口较敏感，因此 RainyOCR 会自动避开高风险的透明无边框组合，回退到更稳定的原生窗口模式。

如果遇到全局快捷键不可用，请检查系统的辅助功能 / 输入监控权限。

如果程序直接退出且终端显示退出码 `139`，通常表示底层原生崩溃。RainyOCR 会自动写入诊断日志：

```text
~/Library/Logs/RainyOCR/rainyocr.log
~/Library/Logs/RainyOCR/rainyocr-crash.log
```

其中 `rainyocr.log` 记录启动、Qt 警告、截图、托盘、快捷键、OCR / 翻译流程；`rainyocr-crash.log` 由 Python `faulthandler` 写入，用于查看崩溃前所有 Python 线程的栈。需要更详细日志时，可用 `RAINYOCR_DEBUG_LOG=1 uv run python main.py` 启动。

### Linux / Wayland

Wayland 环境下建议安装 `grim`，RainyOCR 会优先使用它完成屏幕截图。Hyprland / 高 DPI 场景下已经加入坐标换算和边缘裁剪兼容。

## 开发与检查

常用检查命令：

```bash
uv run ruff check src/UI src/OCRAgent src/TranslateAgent
uv run pyright src/UI src/OCRAgent src/TranslateAgent
uv run python -m compileall src/UI src/OCRAgent src/TranslateAgent
```

## 项目结构

```text
RainyOCR/
├── main.py                         # 程序入口
├── src/
│   ├── UI/                         # PySide6 UI、窗口、托盘、设置、截图控制
│   ├── OCRAgent/                   # OCR 模型调用
│   ├── TranslateAgent/             # 翻译模型调用
│   └── utils/                      # 环境变量等工具函数
├── images/
│   └── rainyocr_tray_icon.svg      # 应用托盘图标
├── docs/
│   └── design.md                   # 设计与实现方案说明
├── .env.example                    # 配置模板
├── pyproject.toml                  # 项目依赖
└── uv.lock                         # uv 锁定文件
```

## License

MIT License. See [LICENSE](LICENSE).
