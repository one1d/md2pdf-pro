# Iteration 3: 插件系统设计

## 概述
为md2pdf-pro添加插件系统，允许用户扩展功能。

## 功能列表

### 1. 插件接口
- pre_process: 预处理钩子
- post_process: 后处理钩子
- on_convert: 转换钩子

### 2. 内置插件
- table_of_contents: 自动生成目录
- page_numbering: 页码编号
- header_footer: 页眉页脚

### 3. 插件管理
- 列出已加载插件
- 启用/禁用插件
- 插件配置

## 实现计划
1. 创建plugins模块
2. 定义插件接口
3. 实现内置插件
4. 单元测试
