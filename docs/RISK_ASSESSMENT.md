# MD2PDF Pro - 风险评估和缓解计划

> 版本: 1.0.0  
> 日期: 2026-02-28

---

## 一、风险识别

### 1.1 技术风险

| ID | 风险 | 概率 | 影响 | 等级 |
|----|------|------|------|------|
| T1 | Mermaid-CLI渲染失败 | 高 | 高 | 🔴 高 |
| T2 | Tectonic兼容性问题 | 中 | 高 | 🔴 高 |
| T3 | 中文字体缺失 | 中 | 高 | 🔴 高 |
| T4 | 大文件内存溢出 | 低 | 中 | 🟡 中 |
| T5 | 并发竞态条件 | 低 | 中 | 🟡 中 |
| T6 | 跨平台兼容性 | 低 | 中 | 🟡 中 |

### 1.2 项目风险

| ID | 风险 | 概率 | 影响 | 等级 |
|----|------|------|------|------|
| P1 | 需求变更 | 中 | 中 | 🟡 中 |
| P2 | 技术难点低估 | 中 | 高 | 🔴 高 |
| P3 | 测试覆盖不足 | 高 | 中 | 🟡 中 |
| P4 | 依赖版本冲突 | 中 | 中 | 🟡 中 |
| P5 | 文档不完整 | 中 | 低 | 🟢 低 |

---

## 二、详细风险分析

### 2.1 T1: Mermaid-CLI渲染失败

**描述**: Mermaid图表可能因语法错误或版本问题渲染失败

**触发条件**:
- Mermaid代码语法错误
- Mermaid版本不支持某些图表类型
- mmdc命令执行失败

**影响**:
- 转换失败，用户无法获得完整PDF
- 错误信息不明确

**缓解措施**:

```python
# 1. 捕获异常，输出警告而非中断
try:
    await self._render_mermaid(code, output_path)
except Exception as e:
    logger.warning(f"Mermaid渲染失败: {e}, 跳过该图表")
    # 保留原始代码块，不替换

# 2. 版本检测
result = subprocess.run(["mmdc", "--version"], capture_output=True)
version = result.stdout.decode().strip()
if parse_version(version) < parse_version("10.0.0"):
    logger.warning("Mermaid-CLI版本过低，建议升级到10.0.0+")

# 3. 提供降级方案
# 保留原始mermaid代码块，使用--strip-empty-paragraphs处理
```

**应急预案**:
- 跳过失败的图表，保留原始代码块
- 提供--strict模式强制失败

---

### 2.2 T2: Tectonic兼容性问题

**描述**: Tectonic在不同平台行为不一致

**触发条件**:
- LaTeX宏包下载失败
- 字体路径问题
- 内存限制

**影响**:
- PDF生成失败
- 构建时间过长

**缓解措施**:

```python
# 1. 配置Tectonic缓存目录
tectonic_args = [
    "--cache", str(cache_dir),
    "--keep-intermediates",
]

# 2. 添加回退引擎
if config.pdf_engine == "tectonic":
    try:
        result = subprocess.run(["tectonic", "--version"])
    except FileNotFoundError:
        logger.warning("Tectonic未安装，回退到xelatex")
        config.pdf_engine = "xelatex"

# 3. 预下载常用宏包
# 首次运行下载必要宏包
```

---

### 2.3 T3: 中文字体缺失

**描述**: 系统缺少中文字体导致CJK排版失败

**触发条件**:
- 系统未安装中文字体
- 字体名称不正确

**影响**:
- 中文显示为方块
- 编译失败

**缓解措施**:

```python
# 1. 字体检测
def detect_cjk_fonts() -> List[str]:
    """检测系统可用的CJK字体"""
    common_fonts = [
        # macOS
        "PingFang SC",
        "STHeiti",
        # Linux
        "Noto Sans CJK SC",
        "WenQuanYi Micro Hei",
        # Windows
        "Microsoft YaHei",
        "SimSun",
    ]
    available = []
    for font in common_fonts:
        if font_exists(font):
            available.append(font)
    return available

# 2. 配置回退
config.font.cjk_fallback = detect_cjk_fonts()

# 3. doctor命令检查
# md2pdf doctor 检查字体并提示安装
```

---

### 2.4 T4: 大文件内存溢出

**描述**: 处理超大Markdown文件时内存不足

**触发条件**:
- 文件大小 > 10MB
- 并发处理多个大文件

**影响**:
- 进程崩溃
- 系统不稳定

**缓解措施**:

```python
# 1. 流式处理
async def process_large_file(path: Path, chunk_size: int = 64 * 1024):
    """流式读取大文件"""
    async with aiofiles.open(path, 'r') as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk

# 2. 内存监控
import psutil

def check_memory_threshold(threshold: float = 0.85):
    """检查内存使用率"""
    return psutil.virtual_memory().percent / 100 > threshold

# 3. 并发限制
if check_memory_threshold():
    # 降低并发数
    max_workers = max(2, current_workers // 2)
```

---

### 2.5 T5: 并发竞态条件

**描述**: 并发访问共享资源导致数据不一致

**触发条件**:
- 多线程同时写入同一文件
- 缓存并发更新

**影响**:
- 数据损坏
- 转换结果异常

**缓解措施**:

```python
# 1. 文件锁
import fcntl

def write_with_lock(path: Path, content: str):
    with open(path, 'a') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            f.write(content)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

# 2. 异步锁
import asyncio

class SharedCache:
    def __init__(self):
        self._lock = asyncio.Lock()
    
    async def get_or_compute(self, key: str, compute_fn):
        async with self._lock:
            if key in self.cache:
                return self.cache[key]
            value = await compute_fn()
            self.cache[key] = value
            return value

# 3. 进程隔离
# 每个转换任务在独立进程中执行
```

---

### 2.6 T6: 跨平台兼容性

**描述**: Windows/Linux路径处理差异

**触发条件**:
- 文件路径包含特殊字符
- 路径分隔符不一致

**影响**:
- 文件找不到
- 命令执行失败

**缓解措施**:

```python
# 1. 使用pathlib
from pathlib import Path

# 2. 标准化路径
def normalize_path(path: str) -> Path:
    return Path(path).resolve()

# 3. 跨平台命令
# Windows使用start，macOS使用open
if sys.platform == "darwin":
    open_command = "open"
elif sys.platform == "win32":
    open_command = "start"
else:
    open_command = "xdg-open"
```

---

## 三、风险监控

### 3.1 监控指标

| 指标 | 阈值 | 告警 |
|------|------|------|
| 转换错误率 | >2% | 邮件 |
| 平均转换时间 | >5s/文件 | 仪表盘 |
| 内存使用率 | >85% | 仪表盘 |
| Mermaid失败率 | >10% | 邮件 |

### 3.2 告警流程

```
指标异常
    │
    ▼
触发告警 → 记录日志 → 通知团队 → 调查原因 → 实施修复
```

---

## 四、应急响应

### 4.1 问题响应流程

```
发现问题
    │
    ├── P0 (严重): 立即响应，1小时内处理
    │
    ├── P1 (高): 当日处理
    │
    ├── P2 (中): 本周处理
    │
    └── P3 (低): 计划处理
```

### 4.2 回滚策略

```bash
# 发布后发现问题
1. 确认问题范围
2. 评估影响
3. 决定回滚或热修复
4. 执行回滚
5. 通知用户
6. 修复问题
7. 重新发布
```

---

## 五、风险接受标准

### 5.1 可接受风险

| 风险 | 接受条件 |
|------|---------|
| Mermaid小概率失败 | <1%错误率 |
| 首次运行慢 | 预热后正常 |
| 小众平台问题 | 有社区支持 |

### 5.2 不可接受风险

| 风险 | 拒绝条件 |
|------|---------|
| 数据丢失 | 0容忍 |
| 安全漏洞 | 0容忍 |
| 核心功能失败 | >98%成功率 |

---

## 六、持续改进

### 6.1 复盘机制

- 每阶段结束后进行复盘
- 记录问题和建议
- 更新风险清单

### 6.2 学习资源

- 关注Pandoc社区
- 跟踪Mermaid更新
- 参考类似项目
