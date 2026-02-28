# MD2PDF Pro - 项目管理和质量标准

> 版本: 1.0.0  
> 日期: 2026-02-28

---

## 一、代码规范

### 1.1 编码标准

| 标准 | 要求 |
|------|------|
| Python版本 | 3.11+ |
| 代码风格 | Black (line-length: 88) |
| Import排序 | isort |
| 命名规范 | PEP 8 |
| 类型注解 | 必须（公共API） |

### 1.2 Lint规则

```yaml
ruff:
  select:
    - E   # pycodestyle errors
    - F   # Pyflakes
    - W   # pycodestyle warnings
    - I   # isort
    - N   # pep8-naming
    - UP  # pyupgrade
    - B   # flake8-bugbear
    - C4  # flake8-comprehensions
  
  fixable: [E, F, W, I, N, UP, B, C4]
  
  ignore:
    - E501  # line too long (handled by black)
    - B008  # do not perform function calls in argument defaults
```

### 1.3 类型检查

```yaml
mypy:
  strict: true
  python_version: 3.11
  warn_return_any: true
  warn_unused_configs: true
  disallow_untyped_defs: true
  
  # 允许的豁免
  allow_redefinition: false
  check_untyped_defs: true
```

---

## 二、测试标准

### 2.1 测试覆盖率要求

| 模块 | 行覆盖率 | 函数覆盖率 | 分支覆盖率 |
|------|---------|----------|-----------|
| config.py | ≥90% | ≥95% | ≥85% |
| preprocessor.py | ≥85% | ≥90% | ≥80% |
| converter.py | ≥85% | ≥90% | ≥80% |
| parallel.py | ≥80% | ≥85% | ≥75% |
| watcher.py | ≥75% | ≥80% | ≥70% |
| cli.py | ≥80% | ≥85% | ≥75% |
| **总计** | **≥85%** | **≥90%** | **≥80%** |

### 2.2 测试组织

```
tests/
├── unit/
│   ├── test_config.py
│   ├── test_preprocessor.py
│   ├── test_converter.py
│   ├── test_parallel.py
│   ├── test_watcher.py
│   └── test_cli.py
├── integration/
│   ├── test_full_workflow.py
│   ├── test_batch_processing.py
│   └── test_watch_mode.py
├── fixtures/
│   ├── markdown/
│   │   ├── basic.md
│   │   ├── mermaid.md
│   │   ├── latex.md
│   │   └── images.md
│   └── templates/
│       └── custom.latex
└── conftest.py
```

### 2.3 测试命名

```python
# 格式: test_{module}_{functionality}_{expected_behavior}

def test_config_load_from_yaml_file():
    """配置可以从YAML文件加载"""
    pass

def test_converter_produces_valid_pdf():
    """转换器生成有效的PDF文件"""
    pass

def test_preprocessor_renders_mermaid_flowchart():
    """预处理器正确渲染Mermaid流程图"""
    pass
```

---

## 三、文档标准

### 3.1 代码文档

| 元素 | 要求 |
|------|------|
| 模块docstring | 1行概要 + 详细说明 |
| 类docstring | 描述类职责、用法 |
| 方法docstring | 参数、返回值、异常 |
| 复杂逻辑 | 行内注释说明 |

### 3.2 文档结构

```python
"""模块名称.

详细描述模块功能和用途。

主要类/函数:
    - ClassName: 类用途说明
    - function_name(): 函数用途说明

示例:
    >>> from md2pdf_pro import module
    >>> module.example()
"""

class ClassName:
    """类用途说明.
    
    详细描述类的职责和使用方式。
    
    属性:
        attr1: 属性1说明
        attr2: 属性2说明
    """
    
    def method(self, param: Type) -> ReturnType:
        """方法用途说明.
        
        参数:
            param: 参数说明
        
        返回:
            返回值说明
        
        异常:
            ValueError: 何时抛出
        
        示例:
            >>> obj = ClassName()
            >>> obj.method("value")
        """
        pass
```

---

## 四、版本管理

### 4.1 分支策略

```
main
│
├── develop (功能开发)
│   │
│   ├── feature/xxx 功能分支
│   │
│   └── bugfix/xxx 修复分支
│
└── release/x.y.z 发布分支
```

### 4.2 提交规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

| 类型 | 说明 |
|------|------|
| feat | 新功能 |
| fix | Bug修复 |
| docs | 文档 |
| style | 格式 |
| refactor | 重构 |
| test | 测试 |
| chore | 维护 |

### 4.3 版本号

```
MAJOR.MINOR.PATCH[-prerelease]

- MAJOR: 不兼容变更
- MINOR: 新功能（向后兼容）
- PATCH: Bug修复
- prerelease: alpha/beta/rc
```

---

## 五、持续集成

### 5.1 CI流程

```yaml
# GitHub Actions
on: [push, pull_request]

jobs:
  lint:
    - ruff check
    - mypy
    - black --check
  
  test:
    - pytest --cov
    - min coverage: 85%
  
  build:
    - python -m build
    - upload artifact
  
  publish:
    - twine upload (on tag)
```

### 5.2 发布流程

```bash
# 1. 更新版本
bump2version patch  # 或 minor/major

# 2. 更新CHANGELOG
git changelog

# 3. 提交
git add -A
git commit -m "Release v1.0.0"

# 4. 标签
git tag -a v1.0.0 -m "Release v1.0.0"

# 5. 发布
git push && git push --tags
```

---

## 六、项目管理

### 6.1 工具链

| 工具 | 用途 |
|------|------|
| Git | 版本控制 |
| GitHub | 代码托管 |
| GitHub Issues | 问题跟踪 |
| GitHub Actions | CI/CD |
| PyPI | 包发布 |
| ReadTheDocs | 文档托管 |

### 6.2 工作流程

```
发现 → 规划 → 开发 → 审查 → 测试 → 部署 → 发布
```

### 6.3 审查标准

| 检查项 | 要求 |
|--------|------|
| 代码风格 | 通过lint |
| 类型检查 | 通过mypy |
| 测试 | 新代码有测试 |
| 文档 | 公共API有docstring |
| 冲突 | 无合并冲突 |

---

## 七、监控和维护

### 7.1 日志级别

| 级别 | 用途 |
|------|------|
| DEBUG | 详细调试信息 |
| INFO | 常规操作信息 |
| WARNING | 警告信息 |
| ERROR | 错误信息 |
| CRITICAL | 严重错误 |

### 7.2 监控指标

| 指标 | 告警阈值 |
|------|---------|
| CPU使用率 | >85% |
| 内存使用率 | >85% |
| 错误率 | >5% |
| 响应时间 | P99 > 5s |

---

## 八、应急响应

### 8.1 问题分类

| 级别 | 响应时间 | 处理方式 |
|------|---------|---------|
| P0-Critical | 1h | 立即处理 |
| P1-High | 4h | 当日处理 |
| P2-Medium | 24h | 本周处理 |
| P3-Low | 72h | 计划处理 |

### 8.2 回滚流程

```bash
# 1. 识别问题
git log --oneline -20

# 2. 回滚版本
git revert <commit>

# 3. 部署稳定版本
git checkout v1.x.y
pip install md2pdf-pro==1.x.y
```
