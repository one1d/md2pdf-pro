# Iteration 2: 模板系统设计

## 概述
为md2pdf-pro添加模板系统，支持用户自定义Pandoc模板。

## 功能列表

### 1. 模板管理
- 列出内置模板
- 列出用户模板
- 验证模板有效性

### 2. 内置模板
- default: 默认Pandoc模板
- academic: 学术论文模板
- report: 报告模板
- presentation: 演示文稿模板

### 3. 自定义模板
- 从文件加载模板
- 模板变量定义
- 模板继承

## 配置更新

```yaml
pandoc:
  template: path/to/template.latex
  template_vars:
    documentclass: article
    fontsize: 12pt
```

## CLI命令
- `md2pdf templates list` - 列出可用模板
- `md2pdf templates validate <template>` - 验证模板

## 实现计划
1. 创建templates模块
2. 添加模板配置
3. 添加CLI命令
4. 单元测试
