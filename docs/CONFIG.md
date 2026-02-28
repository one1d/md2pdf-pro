# MD2PDF Pro 配置详解

> 本文档详细介绍 MD2PDF Pro 的所有配置选项，帮助用户深入理解和灵活配置转换器。

---

## 目录

1. [配置概述](#配置概述)
2. [配置文件](#配置文件)
3. [配置加载优先级](#配置加载优先级)
4. [配置项详解](#配置项详解)
   - [MermaidConfig](#mermaidconfig- mermaid-图表配置)
   - [PandocConfig](#pandocconfig- pandoc-转换配置)
   - [ProcessingConfig](#processingconfig- 处理配置)
   - [FontConfig](#fontconfig- 字体配置)
   - [OutputConfig](#outputconfig- 输出配置)
   - [LoggingConfig](#loggingconfig- 日志配置)
   - [ProjectConfig](#projectconfig- 项目主配置)
5. [环境变量](#环境变量)
6. [配置示例](#配置示例)
7. [最佳实践](#最佳实践)

---

## 配置概述

MD2PDF Pro 使用 **Pydantic** 进行配置管理，提供类型安全、验证完善的配置系统。配置分为以下类别：

| 配置类 | 作用 |
|--------|------|
| `MermaidConfig` | Mermaid 图表渲染设置 |
| `PandocConfig` | Pandoc 文档转换设置 |
| `ProcessingConfig` | 并行处理和性能设置 |
| `FontConfig` | PDF 字体配置 |
| `OutputConfig` | 输出文件和目录设置 |
| `LoggingConfig` | 日志记录配置 |
| `ProjectConfig` | 顶级配置容器 |

---

## 配置文件

### 配置文件位置

MD2PDF Pro 按以下优先级查找配置文件：

```
1. 命令行 --config 参数指定的路径
2. ./md2pdf.yaml          (当前目录)
3. ./.md2pdf.yaml         (隐藏文件)
4. ~/.md2pdf/config.yaml  (用户主目录)
5. 内置默认值
```

### 创建配置文件

```bash
# 在当前目录创建默认配置文件
md2pdf init

# 指定路径创建
md2pdf init --path ./my-config.yaml
```

### YAML 格式

配置文件使用 YAML 格式，支持以下特性：

- 注释以 # 开头
- 支持嵌套结构
- 字符串不需要引号（除非包含特殊字符）
- 布尔值：true / false

---

## 配置加载优先级

配置按以下优先级依次覆盖（后者优先）：

```
默认值 < 环境变量 < 配置文件 < CLI参数
```

---

## 配置项详解

### MermaidConfig (Mermaid 图表配置)

控制 Mermaid 图表的渲染行为。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| theme | MermaidTheme | default | 图表主题 |
| format | MermaidFormat | pdf | 输出格式 |
| width | int | 1200 | 图表宽度(像素) |
| background | str | white | 背景颜色 |
| cache_ttl | int | 86400 | 缓存有效期(秒) |
| output_dir | Path | ~/.cache/md2pdf/mermaid | 缓存目录 |

#### MermaidTheme 可选值

| 值 | 说明 |
|-----|------|
| default | 默认浅色主题 |
| dark | 深色主题 |
| forest | 森林主题 |
| neutral | 中性主题 |

#### MermaidFormat 可选值

| 值 | 说明 |
|-----|------|
| pdf | PDF 向量格式 |
| svg | SVG 矢量格式 |

#### 示例

```yaml
mermaid:
  theme: dark           # 使用深色主题
  format: pdf          # 输出PDF
  width: 1600          # 更宽的图表
  background: "#1e1e1e"  # 深色背景
  cache_ttl: 604800    # 缓存7天
  output_dir: ./cache/mermaid
```

---

### PandocConfig (Pandoc 转换配置)

控制 Pandoc 文档转换的核心行为。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| pdf_engine | PdfEngine | tectonic | PDF 引擎 |
| template | Optional[Path] | None | 自定义模板路径 |
| highlight_style | str | tango | 代码高亮主题 |
| math_engine | MathEngine | mathspec | 数学公式引擎 |
| extra_vars | Dict[str, Any] | {} | 额外变量 |
| standalone | bool | true | 生成独立文档 |
| toc | bool | false | 生成目录 |
| toc_depth | int | 3 | 目录深度 |

#### PdfEngine 可选值

| 值 | 说明 | 平台支持 |
|-----|------|----------|
| tectonic | 现代 TeX 引擎，自动下载宏包 | 跨平台 |
| xelatex | XeLaTeX 引擎 | 跨平台 |
| lualatex | LuaLaTeX 引擎 | 跨平台 |

推荐使用 tectonic，它是最新、最现代的选择，无需手动安装 TeX 发行版。

#### MathEngine 可选值

| 值 | 说明 |
|-----|------|
| mathspec | 使用 LaTeX mathspec 宏包 |
| katex | 使用 KaTeX (需要 JS) |
| mathjax | 使用 MathJax (需要 JS) |

#### highlight_style 可选值

常用值：pygments, tango, espresso, zenburn, monokai, solarized-dark, solarized-light

#### 示例

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

### ProcessingConfig (处理配置)

控制并发处理和性能相关的行为。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| max_workers | int | 8 | 最大并发任务数 |
| batch_size | int | 50 | 批处理大小 |
| timeout | int | 300 | 单文件超时(秒) |
| retry_attempts | int | 3 | 失败重试次数 |
| retry_backoff | float | 2.0 | 重试退避系数 |
| cpu_threshold | int | 80 | CPU 阈值(%) |
| memory_limit | int | 4096 | 内存限制(MB) |

#### 参数详解

- max_workers: 同时处理的文件数量。建议设置为 CPU 核心数的 2 倍。
- timeout: 单个文件转换的最大允许时间。复杂文档可能需要更长。
- retry_attempts: 转换失败时的重试次数。
- retry_backoff: 重试间隔 = retry_backoff ^ attempt 秒。
- cpu_threshold: 触发降速的 CPU 使用率阈值。
- memory_limit: 单个进程的最大内存使用。

#### 示例

```yaml
processing:
  max_workers: 16        # 高性能机器
  batch_size: 100        # 大批量处理
  timeout: 600           # 复杂文档10分钟
  retry_attempts: 5      # 更多重试
  retry_backoff: 1.5     # 快速重试
  cpu_threshold: 70      # 更早降速
  memory_limit: 2048     # 限制内存
```

---

### FontConfig (字体配置)

控制 PDF 中的字体显示。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| cjk_primary | str | PingFang SC | 主中文字体 |
| cjk_fallback | List[str] | 见下文 | 中文字体回退列表 |
| latin_primary | str | Latin Modern Roman | 主西文字体 |
| monospace | str | Menlo | 等宽字体 |
| geometry_margin | str | 2.5cm | 页面边距 |

#### CJK 字体回退列表默认值

- STHeiti (macOS 黑体)
- Noto Sans CJK SC (Linux)
- WenQuanYi Micro Hei (Linux)
- Microsoft YaHei (Windows)

#### 各平台推荐字体

macOS:
```yaml
font:
  cjk_primary: "PingFang SC"
  latin_primary: "Latin Modern Roman"
  monospace: "Menlo"
```

Linux:
```yaml
font:
  cjk_primary: "Noto Sans CJK SC"
  latin_primary: "Latin Modern Roman"
  monospace: "JetBrains Mono"
```

Windows:
```yaml
font:
  cjk_primary: "Microsoft YaHei"
  latin_primary: "Times New Roman"
  monospace: "Consolas"
```

#### 示例

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

### OutputConfig (输出配置)

控制输出文件的生成和行为。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| output_dir | Path | ./output | 输出目录 |
| temp_dir | Path | /tmp/md2pdf | 临时文件目录 |
| naming_pattern | str | {stem}.pdf | 命名模式 |
| preserve_temp | bool | false | 保留临时文件 |
| optimize_pdf | bool | true | 优化 PDF |
| create_subdirs | bool | false | 保持子目录结构 |

#### naming_pattern 可用变量

| 变量 | 说明 |
|------|------|
| {stem} | 原文件名（不含扩展名） |
| {ext} | 原文件扩展名 |
| {parent} | 父目录名 |
| {date} | 日期 (YYYY-MM-DD) |
| {time} | 时间 (HH-MM-SS) |

#### 示例

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

### LoggingConfig (日志配置)

控制日志记录行为。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| level | LogLevel | INFO | 日志级别 |
| format | str | [%(levelname)s] %(message)s | 日志格式 |
| file | Optional[Path] | None | 日志文件路径 |
| rotation | str | daily | 日志轮转策略 |
| max_bytes | int | 10485760 | 单文件最大字节 |
| backup_count | int | 7 | 保留备份数 |

#### LogLevel 可选值

| 值 | 说明 |
|-----|------|
| DEBUG | 详细调试信息 |
| INFO | 常规信息 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |

#### rotation 可选值

| 值 | 说明 |
|-----|------|
| daily | 每天一个新文件 |
| size | 按文件大小轮转 |
| none | 不轮转 |

#### 日志格式变量

| 变量 | 说明 |
|------|------|
| %(levelname)s | 日志级别 |
| %(message)s | 日志消息 |
| %(asctime)s | 时间戳 |
| %(name)s | 日志器名称 |
| %(filename)s | 文件名 |
| %(lineno)d | 行号 |

#### 示例

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

### ProjectConfig (项目主配置)

顶级配置容器，包含所有子配置和文件匹配规则。

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| version | str | 1.0.0 | 配置版本 |
| mermaid | MermaidConfig | 默认值 | Mermaid 配置 |
| pandoc | PandocConfig | 默认值 | Pandoc 配置 |
| processing | ProcessingConfig | 默认值 | 处理配置 |
| font | FontConfig | 默认值 | 字体配置 |
| output | OutputConfig | 默认值 | 输出配置 |
| logging | LoggingConfig | 默认值 | 日志配置 |
| input_patterns | List[str] | [*.md, *.markdown] | 输入文件模式 |
| ignore_patterns | List[str] | 见下文 | 忽略模式 |

#### ignore_patterns 默认值

- .* (隐藏文件)
- _* (以下划线开头)
- node_modules (npm 目录)
- .git (Git 目录)
- __pycache__ (Python 缓存)

#### 示例

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

## 环境变量

可以通过环境变量覆盖默认配置：

| 环境变量 | 对应配置 | 说明 |
|----------|----------|------|
| MD2PDF_PDF_ENGINE | pandoc.pdf_engine | PDF 引擎 |
| MD2PDF_MAX_WORKERS | processing.max_workers | 最大并发数 |
| MD2PDF_OUTPUT_DIR | output.output_dir | 输出目录 |
| MD2PDF_LOG_LEVEL | logging.level | 日志级别 |

#### 示例

```bash
# Linux/macOS
export MD2PDF_PDF_ENGINE=tectonic
export MD2PDF_MAX_WORKERS=16
export MD2PDF_OUTPUT_DIR=./dist
export MD2PDF_LOG_LEVEL=DEBUG
```

---

## 配置示例

### 最小配置

```yaml
pandoc:
  pdf_engine: tectonic
```

### 标准配置

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

### 高性能配置

```yaml
mermaid:
  cache_ttl: 604800  # 7天

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

### 开发者配置

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

## 最佳实践

### 1. 使用配置文件而非命令行参数

配置文件提供更完整的控制，且易于版本管理和共享：

```bash
# 推荐
md2pdf batch "*.md" -c md2pdf.yaml -o output/

# 仅用于快速测试
md2pdf convert doc.md -o output/
```

### 2. 根据机器配置调整并发数

| 机器配置 | max_workers |
|----------|-------------|
| 4核 CPU | 8 |
| 8核 CPU | 16 |
| 16核 CPU | 32 |

### 3. 合理设置缓存时间

- 开发阶段：cache_ttl: 3600 (1小时)
- 生产环境：cache_ttl: 604800 (7天)

### 4. 保持临时目录清洁

```yaml
output:
  temp_dir: /tmp/md2pdf
  preserve_temp: false  # 转换后删除临时文件
```

### 5. 分离开发和生产配置

```bash
# 开发
md2pdf batch "*.md" -c dev.yaml

# 生产
md2pdf batch "*.md" -c prod.yaml
```

---

## 故障排查

### 常见配置问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 中文显示方块 | 字体未安装 | 安装中文字体或更改 cjk_primary |
| Mermaid 渲染失败 | mmdc 未安装 | npm install -g @mermaid-js/mermaid-cli |
| PDF 生成失败 | PDF 引擎问题 | 检查 pdf_engine 设置 |
| 转换超时 | 文件过大 | 增加 timeout 值 |

### 验证配置

```bash
# 显示当前配置
md2pdf config-show

# 验证配置文件
md2pdf config-show -c your-config.yaml
```
