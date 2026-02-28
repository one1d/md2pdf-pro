# MD2PDF Pro

> 批量Markdown转PDF转换器 | Batch Markdown to PDF Converter

**状态**: 开发中 | **版本**: 1.0.0

---

## 功能特性

- [x] Markdown → PDF 批量转换
- [x] LaTeX 数学公式渲染
- [x] Mermaid 图表渲染
- [x] 代码高亮
- [x] 中文排版支持
- [x] 并行处理
- [x] 文件监控 (Watch模式)
- [x] CLI 命令行工具

---

## 快速开始

### 安装依赖

```bash
# 安装Python依赖
pip install -e .

# 安装系统依赖
brew install pandoc tectonic graphviz librsvg node
npm install -g @mermaid-js/mermaid-cli
```

### 使用方法

```bash
# 单文件转换
md2pdf convert document.md -o output/

# 批量转换
md2pdf batch "*.md" -o output/

# 监听模式
md2pdf watch ./docs -o output/

# 环境检查
md2pdf doctor
```

---

## 项目结构

```
md2pdf-pro/
├── src/md2pdf_pro/
│   ├── __init__.py      # 包初始化
│   ├── config.py         # 配置管理 (Pydantic)
│   ├── preprocessor.py   # Mermaid预处理
│   ├── converter.py      # Pandoc转换引擎
│   ├── parallel.py       # 并行处理
│   ├── watcher.py        # 文件监控
│   └── cli.py            # CLI入口
├── tests/
│   ├── conftest.py       # pytest配置
│   ├── unit/             # 单元测试
│   └── integration/      # 集成测试
├── docs/                 # 技术文档
├── pyproject.toml        # 项目配置
├── requirements.txt      # Python依赖
└── Makefile             # 构建脚本
```

---

## 开发
## 开发

```bash
# 安装开发环境
make dev

# 运行测试
make test

# 代码检查
make lint

# 格式化代码
make format
```

---

## 许可证

MIT License
