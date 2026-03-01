# Iteration 1: PDF高级功能设计

## 概述
为md2pdf-pro添加PDF优化功能，包括压缩、元数据和水印。

## 功能列表

### 1. PDF压缩
- 支持三种压缩级别: web, screen, ebook, print, prepress
- 默认使用screen级别(平衡质量和大小)
- 通过命令行参数启用

### 2. PDF元数据
- 支持设置: title, author, subject, keywords, creator
- 从配置文件读取或命令行参数覆盖

### 3. 水印功能
- 支持文本水印
- 可配置位置、透明度、旋转角度
- 支持页眉/页脚

## 配置更新

```yaml
pdf:
  compression: screen  # web|screen|ebook|print|prepress
  metadata:
    author: ""
    title: ""
    subject: ""
    keywords: ""
  watermark:
    enabled: false
    text: "CONFIDENTIAL"
    opacity: 0.3
    position: center  # center|header|footer
    angle: 45
```

## CLI参数
- `--compression`: 压缩级别
- `--author`: 作者
- `--title`: 文档标题
- `--watermark`: 启用水印
- `--watermark-text`: 水印文本

## 实现计划

1. 更新config.py - 添加新配置模型
2. 更新converter.py - 集成Ghostscript处理
3. 添加单元测试
4. 更新文档
