# MD2PDF Pro 配置详解 | Configuration Guide

> 本文档详细介绍 MD2PDF Pro 的所有配置选项 | This document provides detailed configuration options for MD2PDF Pro

---

## 目录 | Table of Contents

1. [配置概述 | Overview](#配置概述--overview)
2. [配置文件 | Configuration Files](#配置文件--configuration-files)
3. [配置加载优先级 | Load Priority](#配置加载优先级--load-priority)
4. [配置项详解 | Configuration Details](#配置项详解--configuration-details)
   - [MermaidConfig](#mermaidconfig--mermaid-configuration)
   - [PandocConfig](#pandocconfig--pandoc-configuration)
   - [ProcessingConfig](#processingconfig--processing-configuration)
   - [FontConfig](#fontconfig--font-configuration)
   - [OutputConfig](#outputconfig--output-configuration)
   - [LoggingConfig](#loggingconfig--logging-configuration)
   - [ProjectConfig](#projectconfig--project-configuration)
5. [环境变量 | Environment Variables](#环境变量--environment-variables)
6. [配置示例 | Examples](#配置示例--examples)
7. [最佳实践 | Best Practices](#最佳实践--best-practices)

---

## 配置概述 | Overview

MD2PDF Pro 使用 **Pydantic** 进行配置管理，提供类型安全、验证完善的配置系统。

MD2PDF Pro uses **Pydantic** for configuration management, providing type-safe and validated configuration.

| 配置类 | Configuration Class | 作用 | Function |
|--------|-------------------|------|----------|
| `MermaidConfig` | MermaidConfig | Mermaid 图表渲染设置 | Mermaid diagram rendering settings |
| `PandocConfig` | PandocConfig | Pandoc 文档转换设置 | Pandoc document conversion settings |
| `ProcessingConfig` | ProcessingConfig | 并行处理和性能设置 | Parallel processing and performance settings |
| `FontConfig` | FontConfig | PDF 字体配置 | PDF font configuration |
| `OutputConfig` | OutputConfig | 输出文件和目录设置 | Output file and directory settings |
| `LoggingConfig` | LoggingConfig | 日志记录配置 | Logging configuration |
| `ProjectConfig` | ProjectConfig | 顶级配置容器 | Top-level configuration container |

---

## 配置文件 | Configuration Files

### 配置文件位置 | Configuration File Locations

MD2PDF Pro 按以下优先级查找配置文件：

MD2PDF Pro searches for configuration files in the following priority order:

```
1. 命令行 --config 参数指定的路径 | Command line --config parameter path
2. ./md2pdf.yaml (当前目录 | current directory)
3. ./.md2pdf.yaml (隐藏文件 | hidden file)
4. ~/.md2pdf/config.yaml (用户主目录 | user home directory)
5. 内置默认值 | Built-in defaults
```

### 创建配置文件 | Create Configuration File

```bash
# 在当前目录创建默认配置文件 | Create default config in current directory
md2pdf init

# 指定路径创建 | Create at specified path
md2pdf init --path ./my-config.yaml
```

### YAML 格式 | YAML Format

配置文件使用 YAML 格式：

Configuration files use YAML format:

- 注释以 # 开头 | Comments start with #
- 支持嵌套结构 | Supports nested structures
- 字符串不需要引号（除非包含特殊字符）| Strings don't need quotes (unless special characters)
- 布尔值：true / false | Boolean values: true / false

---

## 配置加载优先级 | Configuration Load Priority

配置按以下优先级依次覆盖（后者优先）：

Configuration is applied in the following priority order (later takes precedence):

```
默认值 < 环境变量 < 配置文件 < CLI参数
Defaults < Environment Variables < Config File < CLI Arguments
```

---

## 配置项详解 | Configuration Details

### MermaidConfig (Mermaid 图表配置 | Mermaid Configuration)

控制 Mermaid 图表的渲染行为。

Controls Mermaid diagram rendering behavior.

| 字段 | Field | 类型 | Type | 默认值 | Default | 说明 | Description |
|------|-------|------|------|--------|---------|------|-------------|
| theme | theme | MermaidTheme | MermaidTheme | default | default | 图表主题 | Diagram theme |
| format | format | MermaidFormat | MermaidFormat | pdf | pdf | 输出格式 | Output format |
| width | width | int | int | 1200 | 1200 | 图表宽度(像素) | Diagram width (pixels) |
| background | background | str | str | white | white | 背景颜色 | Background color |
| cache_ttl | cache_ttl | int | int | 86400 | 86400 | 缓存有效期(秒) | Cache TTL (seconds) |
| output_dir | output_dir | Path | Path | ~/.cache/md2pdf/mermaid | ~/.cache/md2pdf/mermaid | 缓存目录 | Cache directory |

#### MermaidTheme 可选值 | MermaidTheme Options

| 值 | Value | 说明 | Description |
|----|-------|------|-------------|
| default | default | 默认浅色主题 | Default light theme |
| dark | dark | 深色主题 | Dark theme |
| forest | forest | 森林主题 | Forest theme |
| neutral | neutral | 中性主题 | Neutral theme |

#### MermaidFormat 可选值 | MermaidFormat Options

| 值 | Value | 说明 | Description |
|----|-------|------|-------------|
| pdf | pdf | PDF 向量格式 | PDF vector format |
| svg | svg | SVG 矢量格式 | SVG vector format |

#### 示例 | Example

```yaml
mermaid:
  theme: dark           # 使用深色主题 | Use dark theme
  format: pdf          # 输出PDF | Output PDF
  width: 1600          # 更宽的图表 | Wider diagram
  background: "#1e1e1e"  # 深色背景 | Dark background
  cache_ttl: 604800    # 缓存7天 | Cache for 7 days
  output_dir: ./cache/mermaid
```

---

### PandocConfig (Pandoc 转换配置 | Pandoc Configuration)

控制 Pandoc 文档转换的核心行为。

Controls Pandoc document conversion core behavior.

| 字段 | Field | 类型 | Type | 默认值 | Default | 说明 | Description |
|------|-------|------|------|--------|---------|------|-------------|
| pdf_engine | pdf_engine | PdfEngine | PdfEngine | tectonic | tectonic | PDF 引擎 | PDF engine |
| template | template | Optional[Path] | Optional[Path] | None | None | 自定义模板路径 | Custom template path |
| highlight_style | highlight_style | str | str | tango | tango | 代码高亮主题 | Code highlight style |
| math_engine | math_engine | MathEngine | MathEngine | mathspec | mathspec | 数学公式引擎 | Math formula engine |
| extra_vars | extra_vars | Dict[str, Any] | Dict[str, Any] | {} | {} | 额外变量 | Extra variables |
| standalone | standalone | bool | bool | true | true | 生成独立文档 | Generate standalone document |
| toc | toc | bool | bool | false | false | 生成目录 | Generate table of contents |
| toc_depth | toc_depth | int | int | 3 | 3 | 目录深度 | TOC depth |

#### PdfEngine 可选值 | PdfEngine Options

| 值 | Value | 说明 | Description | 平台支持 | Platform Support |
|----|-------|------|-------------|----------|------------------|
| tectonic | tectonic | 现代 TeX 引擎，自动下载宏包 | Modern TeX engine, auto-downloads packages | 跨平台 | Cross-platform |
| xelatex | xelatex | XeLaTeX 引擎 | XeLaTeX engine | 跨平台 | Cross-platform |
| lualatex | lualatex | LuaLaTeX 引擎 | LuaLaTeX engine | 跨平台 | Cross-platform |

推荐使用 tectonic，它是最新、最现代的选择，无需手动安装 TeX 发行版。

Recommended: tectonic - it's the latest and most modern choice, no manual TeX distribution needed.

#### MathEngine 可选值 | MathEngine Options

| 值 | Value | 说明 | Description |
|----|-------|------|-------------|
| mathspec | mathspec | 使用 LaTeX mathspec 宏包 | Use LaTeX mathspec package |
| katex | katex | 使用 KaTeX (需要 JS) | Use KaTeX (requires JS) |
| mathjax | mathjax | 使用 MathJax (需要 JS) | Use MathJax (requires JS) |

#### highlight_style 可选值 | highlight_style Options

常用值：pygments, tango, espresso, zenburn, monokai, solarized-dark, solarized-light

Common values: pygments, tango, espresso, zenburn, monokai, solarized-dark, solarized-light

#### 示例 | Example

```yaml
pandoc:
  pdf_engine: tectonic
  template: ./templates/eisvogel.latex
  highlight_style: monokai
  math_engine: mathspec
  standalone: true
  toc: true
  toc_depth: 3
  extra_vars:
    documentclass: article
    classoption: oneside
```

---

### ProcessingConfig (处理配置 | Processing Configuration)

控制并发处理和性能相关的行为。

Controls concurrent processing and performance-related behavior.

| 字段 | Field | 类型 | Type | 默认值 | Default | 说明 | Description |
|------|-------|------|------|--------|---------|------|-------------|
| max_workers | max_workers | int | int | 8 | 8 | 最大并发任务数 | Max concurrent tasks |
| batch_size | batch_size | int | int | 50 | 50 | 批处理大小 | Batch size |
| timeout | timeout | int | int | 300 | 300 | 单文件超时(秒) | Single file timeout (seconds) |
| retry_attempts | retry_attempts | int | int | 3 | 3 | 失败重试次数 | Retry attempts on failure |
| retry_backoff | retry_backoff | float | float | 2.0 | 2.0 | 重试退避系数 | Retry backoff factor |
| cpu_threshold | cpu_threshold | int | int | 80 | 80 | CPU 阈值(%) | CPU threshold (%) |
| memory_limit | memory_limit | int | int | 4096 | 4096 | 内存限制(MB) | Memory limit (MB) |

#### 参数详解 | Parameter Details

- **max_workers**: 同时处理的文件数量。建议设置为 CPU 核心数的 2 倍。| Concurrent file processing count. Recommended: 2x CPU cores.
- **timeout**: 单个文件转换的最大允许时间。复杂文档可能需要更长。| Max allowed time for single file conversion. Complex docs may need more.
- **retry_attempts**: 转换失败时的重试次数。| Retry count on conversion failure.
- **retry_backoff**: 重试间隔 = retry_backoff ^ attempt 秒。| Retry interval = retry_backoff ^ attempt seconds.
- **cpu_threshold**: 触发降速的 CPU 使用率阈值。| CPU usage threshold to trigger throttling.
- **memory_limit**: 单个进程的最大内存使用。| Max memory per process.

#### 示例 | Example

```yaml
processing:
  max_workers: 16        # 高性能机器 | High performance machine
  batch_size: 100        # 大批量处理 | Large batch processing
  timeout: 600           # 复杂文档10分钟 | Complex docs: 10 minutes
  retry_attempts: 5      # 更多重试 | More retries
  retry_backoff: 1.5     # 快速重试 | Fast retry
  cpu_threshold: 70      # 更早降速 | Earlier throttling
  memory_limit: 2048     # 限制内存 | Limit memory
```

---

### FontConfig (字体配置 | Font Configuration)

控制 PDF 中的字体显示。

Controls PDF font rendering.

| 字段 | Field | 类型 | Type | 默认值 | Default | 说明 | Description |
|------|-------|------|------|--------|---------|------|-------------|
| cjk_primary | cjk_primary | str | str | PingFang SC | PingFang SC | 主中文字体 | Primary CJK font |
| cjk_fallback | cjk_fallback | List[str] | List[str] | 见下文 | See below | 中文字体回退列表 | CJK font fallback list |
| latin_primary | latin_primary | str | str | Latin Modern Roman | Latin Modern Roman | 主西文字体 | Primary Latin font |
| monospace | monospace | str | str | Menlo | Menlo | 等宽字体 | Monospace font |
| geometry_margin | geometry_margin | str | str | 2.5cm | 2.5cm | 页面边距 | Page margin |

#### CJK 字体回退列表默认值 | CJK Font Fallback Default

- STHeiti (macOS 黑体 | macOS Heiti)
- Noto Sans CJK SC (Linux)
- WenQuanYi Micro Hei (Linux)
- Microsoft YaHei (Windows)

#### 各平台推荐字体 | Recommended Fonts by Platform

**macOS:**

```yaml
font:
  cjk_primary: "PingFang SC"
  latin_primary: "Latin Modern Roman"
  monospace: "Menlo"
```

**Linux:**

```yaml
font:
  cjk_primary: "Noto Sans CJK SC"
  latin_primary: "Latin Modern Roman"
  monospace: "JetBrains Mono"
```

**Windows:**

```yaml
font:
  cjk_primary: "Microsoft YaHei"
  latin_primary: "Times New Roman"
  monospace: "Consolas"
```

#### 示例 | Example

```yaml
font:
  cjk_primary: "Noto Sans CJK SC"
  cjk_fallback:
    - "WenQuanYi Micro Hei"
    - "Microsoft YaHei"
  latin_primary: "Inter"
  monospace: "JetBrains Mono"
  geometry_margin: "2cm"
```

---

### OutputConfig (输出配置 | Output Configuration)

控制输出文件的生成和行为。

Controls output file generation and behavior.

| 字段 | Field | 类型 | Type | 默认值 | Default | 说明 | Description |
|------|-------|------|------|--------|---------|------|-------------|
| output_dir | output_dir | Path | Path | ./output | ./output | 输出目录 | Output directory |
| temp_dir | temp_dir | Path | Path | /tmp/md2pdf | /tmp/md2pdf | 临时文件目录 | Temp file directory |
| naming_pattern | naming_pattern | str | str | {stem}.pdf | {stem}.pdf | 命名模式 | Naming pattern |
| preserve_temp | preserve_temp | bool | bool | false | false | 保留临时文件 | Preserve temp files |
| optimize_pdf | optimize_pdf | bool | bool | true | true | 优化 PDF | Optimize PDF |
| create_subdirs | create_subdirs | bool | bool | false | false | 保持子目录结构 | Preserve subdirectory structure |

#### naming_pattern 可用变量 | naming_pattern Available Variables

| 变量 | Variable | 说明 | Description |
|------|----------|------|-------------|
| {stem} | {stem} | 原文件名（不含扩展名） | Original filename (without extension) |
| {ext} | {ext} | 原文件扩展名 | Original file extension |
| {parent} | {parent} | 父目录名 | Parent directory name |
| {date} | {date} | 日期 (YYYY-MM-DD) | Date (YYYY-MM-DD) |
| {time} | {time} | 时间 (HH-MM-SS) | Time (HH-MM-SS) |

#### 示例 | Example

```yaml
output:
  output_dir: ./dist
  temp_dir: ./tmp
  naming_pattern: "{parent}/{stem}.pdf"
  preserve_temp: true
  optimize_pdf: true
  create_subdirs: true
```

---

### LoggingConfig (日志配置 | Logging Configuration)

控制日志记录行为。

Controls logging behavior.

| 字段 | Field | 类型 | Type | 默认值 | Default | 说明 | Description |
|------|-------|------|------|--------|---------|------|-------------|
| level | level | LogLevel | LogLevel | INFO | INFO | 日志级别 | Log level |
| format | format | str | str | [%(levelname)s] %(message)s | [%(levelname)s] %(message)s | 日志格式 | Log format |
| file | file | Optional[Path] | Optional[Path] | None | None | 日志文件路径 | Log file path |
| rotation | rotation | str | str | daily | daily | 日志轮转策略 | Log rotation strategy |
| max_bytes | max_bytes | int | int | 10485760 | 10485760 | 单文件最大字节 | Max bytes per file |
| backup_count | backup_count | int | int | 7 | 7 | 保留备份数 | Backup count |

#### LogLevel 可选值 | LogLevel Options

| 值 | Value | 说明 | Description |
|----|-------|------|-------------|
| DEBUG | DEBUG | 详细调试信息 | Detailed debug info |
| INFO | INFO | 常规信息 | General information |
| WARNING | WARNING | 警告信息 | Warning information |
| ERROR | ERROR | 错误信息 | Error information |

#### rotation 可选值 | rotation Options

| 值 | Value | 说明 | Description |
|----|-------|------|-------------|
| daily | daily | 每天一个新文件 | New file daily |
| size | size | 按文件大小轮转 | Rotate by file size |
| none | none | 不轮转 | No rotation |

#### 日志格式变量 | Log Format Variables

| 变量 | Variable | 说明 | Description |
|------|----------|------|-------------|
| %(levelname)s | %(levelname)s | 日志级别 | Log level |
| %(message)s | %(message)s | 日志消息 | Log message |
| %(asctime)s | %(asctime)s | 时间戳 | Timestamp |
| %(name)s | %(name)s | 日志器名称 | Logger name |
| %(filename)s | %(filename)s | 文件名 | Filename |
| %(lineno)d | %(lineno)d | 行号 | Line number |

#### 示例 | Example

```yaml
logging:
  level: DEBUG
  format: "[%(asctime)s] %(name)s - %(levelname)s - %(message)s"
  file: ./logs/md2pdf.log
  rotation: daily
  max_bytes: 5242880
  backup_count: 14
```

---

### ProjectConfig (项目主配置 | Project Configuration)

顶级配置容器，包含所有子配置和文件匹配规则。

Top-level configuration container, containing all sub-configurations and file matching rules.

| 字段 | Field | 类型 | Type | 默认值 | Default | 说明 | Description |
|------|-------|------|------|--------|---------|------|-------------|
| version | version | str | str | 1.0.0 | 1.0.0 | 配置版本 | Config version |
| mermaid | mermaid | MermaidConfig | MermaidConfig | 默认值 | Default | Mermaid 配置 | Mermaid config |
| pandoc | pandoc | PandocConfig | PandocConfig | 默认值 | Default | Pandoc 配置 | Pandoc config |
| processing | processing | ProcessingConfig | ProcessingConfig | 默认值 | Default | 处理配置 | Processing config |
| font | font | FontConfig | FontConfig | 默认值 | Default | 字体配置 | Font config |
| output | output | OutputConfig | OutputConfig | 默认值 | Default | 输出配置 | Output config |
| logging | logging | LoggingConfig | LoggingConfig | 默认值 | Default | 日志配置 | Logging config |
| input_patterns | input_patterns | List[str] | List[str] | [*.md, *.markdown] | [*.md, *.markdown] | 输入文件模式 | Input file patterns |
| ignore_patterns | ignore_patterns | List[str] | List[str] | 见下文 | See below | 忽略模式 | Ignore patterns |

#### ignore_patterns 默认值 | ignore_patterns Default

- .* (隐藏文件 | Hidden files)
- _* (以下划线开头 | Files starting with underscore)
- node_modules (npm 目录 | npm directories)
- .git (Git 目录 | Git directories)
- __pycache__ (Python 缓存 | Python cache)

#### 示例 | Example

```yaml
version: "1.0.0"

mermaid:
  theme: default

pandoc:
  pdf_engine: tectonic
  highlight_style: tango

processing:
  max_workers: 8
  timeout: 300

font:
  cjk_primary: "PingFang SC"

output:
  output_dir: ./output
  temp_dir: /tmp/md2pdf

logging:
  level: INFO

input_patterns:
  - "*.md"
  - "*.markdown"
  - "docs/*.md"

ignore_patterns:
  - ".*"
  - "_*"
  - "node_modules"
  - ".git"
  - "draft_*"
```

---

## 环境变量 | Environment Variables

可以通过环境变量覆盖默认配置：

You can override default configuration with environment variables:

| 环境变量 | Environment Variable | 对应配置 | Corresponding Config | 说明 | Description |
|----------|---------------------|----------|---------------------|------|-------------|
| MD2PDF_PDF_ENGINE | MD2PDF_PDF_ENGINE | pandoc.pdf_engine | pandoc.pdf_engine | PDF 引擎 | PDF engine |
| MD2PDF_MAX_WORKERS | MD2PDF_MAX_WORKERS | processing.max_workers | processing.max_workers | 最大并发数 | Max workers |
| MD2PDF_OUTPUT_DIR | MD2PDF_OUTPUT_DIR | output.output_dir | output.output_dir | 输出目录 | Output directory |
| MD2PDF_LOG_LEVEL | MD2PDF_LOG_LEVEL | logging.level | logging.level | 日志级别 | Log level |

#### 示例 | Example

```bash
# Linux/macOS
export MD2PDF_PDF_ENGINE=tectonic
export MD2PDF_MAX_WORKERS=16
export MD2PDF_OUTPUT_DIR=./dist
export MD2PDF_LOG_LEVEL=DEBUG

# Windows
set MD2PDF_PDF_ENGINE=tectonic
set MD2PDF_MAX_WORKERS=16
```

---

## 配置示例 | Examples

### 最小配置 | Minimal Configuration

```yaml
pandoc:
  pdf_engine: tectonic
```

### 标准配置 | Standard Configuration

```yaml
version: "1.0.0"

mermaid:
  theme: default
  format: pdf
  width: 1200
  cache_ttl: 86400

pandoc:
  pdf_engine: tectonic
  highlight_style: tango
  math_engine: mathspec

processing:
  max_workers: 8
  timeout: 300
  retry_attempts: 3

font:
  cjk_primary: "PingFang SC"

output:
  output_dir: ./output
  temp_dir: /tmp/md2pdf

logging:
  level: INFO
```

### 高性能配置 | High Performance Configuration

```yaml
mermaid:
  cache_ttl: 604800  # 7天 | 7 days

pandoc:
  pdf_engine: tectonic

processing:
  max_workers: 16
  batch_size: 100
  timeout: 600

font:
  cjk_primary: "Noto Sans CJK SC"
  latin_primary: "Inter"

output:
  optimize_pdf: true
```

### 开发者配置 | Developer Configuration

```yaml
mermaid:
  output_dir: ./debug/mermaid

pandoc:
  pdf_engine: tectonic

processing:
  max_workers: 4
  timeout: 60

output:
  preserve_temp: true

logging:
  level: DEBUG
  file: ./debug/md2pdf.log
```

---

## 最佳实践 | Best Practices

### 1. 使用配置文件而非命令行参数 | Use Config File Over CLI Arguments

配置文件提供更完整的管理：

Configuration files provide more complete control:

```bash
# 推荐 | Recommended
md2pdf batch "*.md" -c md2pdf.yaml -o output/

# 仅用于快速测试 | Only for quick testing
md2pdf convert doc.md -o output/
```

### 2. 根据机器配置调整并发数 | Adjust Concurrency Based on Machine

| 机器配置 | Machine | max_workers |
|----------|---------|-------------|
| 4核 CPU | 4-core CPU | 8 |
| 8核 CPU | 8-core CPU | 16 |
| 16核 CPU | 16-core CPU | 32 |

### 3. 合理设置缓存时间 | Set Appropriate Cache TTL

- 开发阶段 | Development: cache_ttl: 3600 (1小时 | 1 hour)
- 生产环境 | Production: cache_ttl: 604800 (7天 | 7 days)

### 4. 保持临时目录清洁 | Keep Temp Directory Clean

```yaml
output:
  temp_dir: /tmp/md2pdf
  preserve_temp: false  # 转换后删除临时文件 | Delete temp files after conversion
```

### 5. 分离开发和生产配置 | Separate Dev and Prod Configs

```bash
# 开发 | Development
md2pdf batch "*.md" -c dev.yaml

# 生产 | Production
md2pdf batch "*.md" -c prod.yaml
```

---

## 故障排查 | Troubleshooting

### 常见配置问题 | Common Configuration Issues

| 问题 | Issue | 原因 | Cause | 解决方案 | Solution |
|------|-------|------|-------|----------|----------|
| 中文显示方块 | Chinese chars show as boxes | 字体未安装 | Font not installed | 安装中文字体或更改 cjk_primary | Install Chinese font or change cjk_primary |
| Mermaid 渲染失败 | Mermaid rendering failed | mmdc 未安装 | mmdc not installed | npm install -g @mermaid-js/mermaid-cli |
| PDF 生成失败 | PDF generation failed | PDF 引擎问题 | PDF engine issue | 检查 pdf_engine 设置 | Check pdf_engine setting |
| 转换超时 | Conversion timeout | 文件过大 | File too large | 增加 timeout 值 | Increase timeout value |

### 验证配置 | Validate Configuration

```bash
# 显示当前配置 | Show current configuration
md2pdf config-show

# 验证配置文件 | Validate config file
md2pdf config-show -c your-config.yaml
```
