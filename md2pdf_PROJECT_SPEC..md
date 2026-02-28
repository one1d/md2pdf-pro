

```markdown
# MD2PDF Pro - 批量Markdown转PDF转换器

## 项目规范文档 (SPEC方法论)
**版本**: 1.0.0  
**日期**: 2026-02-28  
**平台**: macOS (兼容Linux/Windows)  
**核心工具**: Pandoc + Tectonic + Mermaid-CLI  

---

## 📋 目录
1. [Specification (规范)](#1-specification-规范)
2. [Execution (执行)](#2-execution-执行)
3. [Performance (性能)](#3-performance-性能)
4. [Completion (完成)](#4-completion-完成)
5. [附录](#5-附录)

---

## 1. SPECIFICATION (规范)

### 1.1 功能需求矩阵

| 功能模块 | 技术要求 | 实现方案 | 优先级 |
|---------|---------|---------|-------|
| **基础转换** | Markdown → PDF | Pandoc + LaTeX | P0 |
| **数学公式** | LaTeX渲染 (`$...$`, `$$...$$`) | mathspec + amsmath | P0 |
| **流程图** | Mermaid flowchart/sequence/gantt | mmdc (PDF输出) | P0 |
| **思维导图** | Mermaid mindmap v9.2+ | mmdc + PDF矢量图 | P0 |
| **代码高亮** | 语法着色、行号 | skylighting (pandoc内置) | P0 |
| **图片处理** | 本地/Web图片、SVG转PDF | aiohttp + rsvg-convert | P1 |
| **并行处理** | 并发>8文件，CPU>80% | asyncio + semaphore | P0 |
| **中文支持** | CJK字体、竖排支持 | xeCJK + 系统字体 | P1 |

### 1.2 技术架构

```yaml
系统架构:
  输入层:
    - 文件扫描: glob pattern匹配
    - YAML Front Matter解析
    - 元数据注入
  
  预处理层:
    - Mermaid渲染器: 代码块→PDF矢量图
    - 图片下载器: 异步HTTP获取
    - 链接检查器: 验证本地资源
  
  转换层:
    - Pandoc引擎池: 多进程隔离
    - LaTeX编译: Tectonic引擎
    - 模板系统: eisvogel/custom
  
  输出层:
    - PDF优化: 压缩/书签
    - 错误报告: JSON格式日志
    - 通知系统: macOS Notification Center
```

1.3 文件结构规范

```
md2pdf-pro/
├── src/
│   ├── __init__.py
│   ├── cli.py              # Typer命令行接口
│   ├── config.py           # Pydantic配置模型
│   ├── preprocessor.py     # Mermaid/图片预处理
│   ├── converter.py        # Pandoc异步封装
│   ├── parallel.py         # 并发控制器
│   └── watcher.py          # 文件监控
├── filters/
│   └── mermaid.lua         # Pandoc Lua过滤器
├── templates/
│   ├── eisvogel.latex      # 基础模板
│   └── academic.latex      # 学术模板
├── config.yaml             # 默认配置
├── requirements.txt
└── README.md
```

---

2. EXECUTION (执行)

2.1 环境依赖安装

macOS系统要求: macOS 12.0+

前置依赖:

```bash
# 1. 系统级依赖 (Homebrew)
brew install pandoc tectonic graphviz librsvg python@3.11 node

# 2. Node.js工具链
npm install -g @mermaid-js/mermaid-cli

# 3. Python环境
python3.11 -m venv venv
source venv/bin/activate
pip install typer rich aiofiles aiohttp pydantic pyyaml watchdog

# 4. 验证安装
./scripts/doctor.sh
```

2.2 核心模块实现

A. 配置管理 (config.py)

```python
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List, Optional

class MermaidConfig(BaseModel):
    theme: str = "default"  # default, dark, forest, neutral
    format: str = "pdf"     # pdf推荐，避免svg兼容问题
    width: int = 1200
    background: str = "white"
    
class PandocConfig(BaseModel):
    pdf_engine: str = "tectonic"  # 或 xelatex
    template: Optional[Path] = None
    highlight_style: str = "tango"
    extra_vars: dict = Field(default_factory=dict)
    
class ProcessingConfig(BaseModel):
    max_workers: int = 8
    batch_size: int = 50
    timeout: int = 300  # 单文件超时(秒)
    
class ProjectConfig(BaseModel):
    mermaid: MermaidConfig = MermaidConfig()
    pandoc: PandocConfig = PandocConfig()
    processing: ProcessingConfig = ProcessingConfig()
    output_dir: Path = Path("./output")
    temp_dir: Path = Path("/tmp/md2pdf")
```

B. Mermaid预处理器 (preprocessor.py)

```python
import asyncio
import hashlib
import re
from pathlib import Path
from typing import Tuple

class MermaidPreprocessor:
    """将Mermaid代码块渲染为PDF矢量图"""
    
    MERMAID_REGEX = re.compile(r'```mermaid\s*\n(.*?)```', re.DOTALL)
    
    def __init__(self, output_dir: Path, config: MermaidConfig):
        self.output_dir = output_dir / "mermaid"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config
        
    async def process(self, content: str, file_id: str) -> Tuple[str, list]:
        """
        替换markdown中的mermaid代码块为图片引用
        返回: (新内容, 生成的文件列表)
        """
        matches = self.MERMAID_REGEX.findall(content)
        if not matches:
            return content, []
            
        generated_files = []
        new_content = content
        
        for idx, mermaid_code in enumerate(matches):
            # 生成基于内容的hash，避免重复渲染
            code_hash = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
            output_file = self.output_dir / f"{file_id}_{idx}_{code_hash}.pdf"
            
            if not output_file.exists():
                await self._render_mermaid(mermaid_code, output_file)
            
            generated_files.append(output_file)
            
            # 替换代码块为图片引用 (LaTeX格式)
            placeholder = f"```mermaid\n{mermaid_code}```"
            latex_include = f"![]({output_file}){{ width=100% }}"
            new_content = new_content.replace(placeholder, latex_include, 1)
            
        return new_content, generated_files
    
    async def _render_mermaid(self, code: str, output_path: Path):
        """调用mmdc生成PDF (矢量图，无质量损失)"""
        input_file = self.output_dir / f"temp_{output_path.stem}.mmd"
        input_file.write_text(code, encoding='utf-8')
        
        cmd = [
            "mmdc",
            "-i", str(input_file),
            "-o", str(output_path),
            "-w", str(self.config.width),
            "-b", self.config.background,
            "--pdfFit"  # 确保PDF适配页面
        ]
        
        if self.config.theme != "default":
            cmd.extend(["-t", self.config.theme])
            
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        input_file.unlink(missing_ok=True)
        
        if proc.returncode != 0:
            raise RuntimeError(f"Mermaid渲染失败: {stderr.decode()}")
```

C. 异步转换引擎 (converter.py)

```python
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Optional

class PandocEngine:
    def __init__(self, config: PandocConfig):
        self.config = config
        
    async def convert(
        self, 
        input_file: Path, 
        output_file: Path, 
        metadata: Optional[Dict] = None
    ) -> bool:
        """
        异步调用pandoc进行转换
        """
        cmd = [
            "pandoc",
            str(input_file),
            "-o", str(output_file),
            f"--pdf-engine={self.config.pdf_engine}",
            "--standalone",
            "--highlight-style", self.config.highlight_style,
            # 数学公式支持
            "-V", "mathspec=true",
            "-V", "geometry:margin=2.5cm",
            # CJK支持 (macOS系统字体)
            "-V", "CJKmainfont=PingFang SC",
            "-V", "mainfont=Latin Modern Roman",
            "-V", "monofont=Menlo",
        ]
        
        # 添加自定义模板
        if self.config.template:
            cmd.extend(["--template", str(self.config.template)])
            
        # 添加元数据
        if metadata:
            for key, value in metadata.items():
                cmd.extend(["-M", f"{key}={value}"])
        
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), 
                timeout=300
            )
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"转换超时: {input_file}")
            
        if proc.returncode != 0:
            error_msg = stderr.decode()
            raise RuntimeError(f"Pandoc错误: {error_msg}")
            
        return True
```

D. 并行批处理器 (parallel.py)

```python
import asyncio
from pathlib import Path
from typing import List, Callable
from rich.progress import Progress, TaskID

class BatchProcessor:
    def __init__(self, max_workers: int = 8):
        self.semaphore = asyncio.Semaphore(max_workers)
        self.progress = Progress()
        
    async def process_batch(
        self, 
        files: List[Path], 
        process_fn: Callable,
        task_name: str = "Processing"
    ):
        """
        批量处理文件，带进度条
        """
        with self.progress:
            task = self.progress.add_task(
                f"[cyan]{task_name}", 
                total=len(files)
            )
            
            tasks = [
                self._wrap_task(f, process_fn, task) 
                for f in files
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 统计成功/失败
            success = sum(1 for r in results if r is True)
            failures = [r for r in results if isinstance(r, Exception)]
            
            return {"success": success, "failures": failures}
    
    async def _wrap_task(
        self, 
        file: Path, 
        process_fn: Callable, 
        task_id: TaskID
    ):
        async with self.semaphore:
            try:
                result = await process_fn(file)
                self.progress.advance(task_id)
                return result
            except Exception as e:
                self.progress.advance(task_id)
                return e
```

E. 主控制流程 (main.py)

```python
import asyncio
import yaml
from pathlib import Path
from rich.console import Console

console = Console()

class MD2PDFConverter:
    def __init__(self, config_path: Optional[Path] = None):
        self.config = self._load_config(config_path)
        self.preprocessor = MermaidPreprocessor(
            self.config.temp_dir, 
            self.config.mermaid
        )
        self.engine = PandocEngine(self.config.pandoc)
        self.processor = BatchProcessor(self.config.processing.max_workers)
        
    async def convert_file(self, input_file: Path) -> Path:
        """单文件转换流程"""
        file_id = input_file.stem
        temp_dir = Path(tempfile.mkdtemp())
        
        try:
            # 1. 读取原始内容
            content = input_file.read_text(encoding='utf-8')
            
            # 2. 解析YAML Front Matter
            metadata, body = self._parse_front_matter(content)
            
            # 3. 预处理Mermaid
            processed_content, _ = await self.preprocessor.process(body, file_id)
            
            # 4. 保存临时md文件
            temp_md = temp_dir / f"{file_id}.md"
            temp_md.write_text(processed_content, encoding='utf-8')
            
            # 5. 生成PDF
            output_file = self.config.output_dir / f"{file_id}.pdf"
            self.config.output_dir.mkdir(parents=True, exist_ok=True)
            
            await self.engine.convert(temp_md, output_file, metadata)
            
            console.print(f"[green]✓[/green] {input_file.name}")
            return output_file
            
        finally:
            # 清理临时文件
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    async def convert_batch(self, pattern: str):
        """批量转换入口"""
        files = list(Path(".").glob(pattern))
        if not files:
            console.print("[red]未找到匹配文件[/red]")
            return
            
        console.print(f"[blue]发现 {len(files)} 个文件[/blue]")
        
        results = await self.processor.process_batch(
            files, 
            self.convert_file,
            "Converting Markdown"
        )
        
        # 输出报告
        console.print(f"\n[green]成功: {results['success']}[/green]")
        if results['failures']:
            console.print(f"[red]失败: {len(results['failures'])}[/red]")
            for error in results['failures']:
                console.print(f"  - {error}")
```

2.3 CLI接口

```python
import typer
from pathlib import Path

app = typer.Typer(help="MD2PDF Pro - 批量Markdown转PDF工具")

@app.command()
def convert(
    files: List[Path] = typer.Argument(..., help="Markdown文件或通配符"),
    output: Path = typer.Option("./output", "--output", "-o"),
    config: Optional[Path] = typer.Option(None, "--config", "-c"),
    workers: int = typer.Option(8, "--workers", "-w"),
    watch: bool = typer.Option(False, "--watch", help="监听模式")
):
    """转换Markdown文件为PDF"""
    converter = MD2PDFConverter(config)
    
    if watch:
        # 启动文件监控
        from watchdog.observers import Observer
        # ... 实现监控逻辑
    else:
        # 批量处理
        async def run():
            for pattern in files:
                await converter.convert_batch(str(pattern))
        
        asyncio.run(run())

@app.command()
def doctor():
    """检查环境依赖"""
    # 检查pandoc, tectonic, mmdc等
    pass

if __name__ == "__main__":
    app()
```

---

3. PERFORMANCE (性能)

3.1 并发策略

策略选择: 协程+信号量 (I/O为主) + 子进程隔离 (CPU密集型)

```python
# 限制并发数，避免系统过载
semaphore = asyncio.Semaphore(8)

# 对于pandoc调用，使用进程池避免GIL
from concurrent.futures import ProcessPoolExecutor

async def cpu_bound_convert(input_file):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        process_pool, 
        subprocess_run_pandoc, 
        input_file
    )
```

3.2 缓存机制

- Mermaid图表缓存: 基于内容Hash，避免重复渲染相同图表
- 图片下载缓存: URL→本地文件映射，支持离线重试
- LaTeX包缓存: Tectonic自动缓存下载的包到`~/.cache/Tectonic`

3.3 资源优化

优化项	方案	效果	
LaTeX引擎	Tectonic替代TeX Live	体积减少95%，按需下载	
Mermaid输出	PDF矢量格式	避免PNG像素化，文件更小	
图片处理	异步IO	下载与转换并行	
内存管理	流式处理	单文件峰值<500MB	

3.4 性能基准

- 测试环境: MacBook Pro M3, 16GB RAM
- 测试样本: 100个Markdown文件 (平均2MB，含5个Mermaid图表)
- 目标指标:
  - 总耗时: < 120秒
  - 内存峰值: < 4GB
  - CPU利用率: > 75%
  - 成功率: > 98%

---

4. COMPLETION (完成)

4.1 测试策略

```python
# tests/test_integration.py
import pytest
from pathlib import Path

class TestConversion:
    def test_math_formula(self):
        """测试LaTeX公式渲染"""
        input_md = Path("tests/fixtures/math.md")
        result = convert_sync(input_md)
        assert result.exists()
        # 验证PDF包含数学符号
        
    def test_mermaid_flowchart(self):
        """测试流程图渲染"""
        input_md = Path("tests/fixtures/flowchart.md")
        result = convert_sync(input_md)
        assert result.exists()
        
    def test_batch_processing(self):
        """测试批量处理稳定性"""
        files = list(Path("tests/fixtures/batch").glob("*.md"))
        results = batch_convert_sync(files)
        assert len(results['failures']) == 0
```

4.2 交付清单

- 源代码: GitHub仓库，含CI/CD (GitHub Actions)
- 二进制分发: Homebrew Formula
- 文档:
  - README (安装/快速开始)
  - API文档 (pdoc生成)
  - 用户手册 (示例：公式语法、Mermaid示例)
- 配置模板:
  - 学术论文模板 (LaTeX)
  - 技术文档模板
  - 中文书籍模板 (xeCJK配置)

4.3 运维监控

```yaml
# 日志结构
log_format:
  timestamp: ISO8601
  level: INFO/ERROR/WARNING
  file: 输入文件名
  stage: preprocess/convert/cleanup
  duration_ms: 处理耗时
  error: 错误详情 (如有)
```

---

5. 附录

A. 依赖版本锁定

```
pandoc >= 3.1.0
tectonic >= 0.14.0
mermaid-cli >= 10.0.0
Python >= 3.11
```

B. 常见错误排查

错误	原因	解决	
`mmdc: command not found`	Node模块未全局安装	`npm install -g @mermaid-js/mermaid-cli`	
`font-not-found`	LaTeX缺少中文字体	安装`xeCJK`宏包或指定系统字体	
`timeout`	单文件过大	增加`processing.timeout`配置	

C. 参考资源

- [Pandoc Manual](https://pandoc.org/MANUAL.html)
- [Mermaid Diagrams](https://mermaid.js.org/)
- [Tectonic Typesetting](https://tectonic-typesetting.github.io/)

---

文档维护: 如有更新，请同步修改版本号并记录变更日志。

```

