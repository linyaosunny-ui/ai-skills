---
name: xlsx-data-analysis
description: Excel 数据分析工具 - 使用 xlsx2csv 命令行工具将 xlsx 转换为 CSV 格式，便于后续处理和分析。触发词：分析 xlsx 数据、Excel 转 CSV、xlsx 转换、读取 Excel 文件
---

# xlsx-data-analysis - Excel 数据分析工具

## 概述

当需要分析 xlsx 文件数据时，使用本工具将 xlsx 转换为 CSV 格式，便于后续处理和分析。

## 核心工具：xlsx2csv

`xlsx2csv` 是一个轻量级命令行工具，用于将 Excel (.xlsx) 文件转换为 CSV 格式。

## 安装

```bash
pip install xlsx2csv
```

## 使用方法

### 单文件转换

```bash
python -m xlsx2csv "input.xlsx" "output.csv"
```

> **重要**: Windows 环境下，由于 PATH 问题，必须使用 `python -m xlsx2csv` 而非直接调用 `xlsx2csv`。

### 批量转换

```bash
python -m xlsx2csv *.xlsx
```

### 常用参数

| 参数 | 说明 |
|------|------|
| `-s, --sheet` | 指定工作表名称或索引 |
| `-e, --encoding` | 输出编码，默认 utf-8 |
| `-d, --delimiter` | 分隔符，默认逗号 |
| `-n, --no-header` | 不输出表头 |
| `--all` | 转换所有工作表 |

## 完整示例

```bash
# 安装并转换（PowerShell 语法）
pip install xlsx2csv -q; python -m xlsx2csv "D:/path/input.xlsx" "D:/path/output.csv"

# 指定工作表
python -m xlsx2csv --sheet "Sheet1" "input.xlsx" "output.csv"

# 指定编码（解决 Excel 打开乱码）
python -m xlsx2csv --encoding "utf-8-sig" "input.xlsx" "output.csv"
```

## 验证转换结果

转换后检查：

```powershell
# 查看文件信息
Get-Item "output.csv" | Select-Object Name, Length, LastWriteTime

# 查看文件内容
Get-Content "output.csv" -Head 10
```

## Python 备选方案

如果需要更灵活的处理，使用 pandas：

```python
import pandas as pd

# 单文件转换
df = pd.read_excel('input.xlsx')
df.to_csv('output.csv', index=False, encoding='utf-8')

# 批量转换
import os
for file in os.listdir('.'):
    if file.endswith('.xlsx'):
        df = pd.read_excel(file)
        df.to_csv(file.replace('.xlsx', '.csv'), index=False, encoding='utf-8')
```

安装依赖：
```bash
pip install pandas openpyxl
```

## 注意事项

1. **PATH 问题**: Windows 下用 `python -m xlsx2csv` 调用
2. **编码问题**: 默认 UTF-8，Excel 打开乱码用 `utf-8-sig`
3. **多工作表**: 默认只转换第一个工作表
4. **大文件**: 超大文件建议用 pandas 方式

## Skill 进化与知识累积

当发现新的使用场景或问题时，更新本 Skill：

1. **新发现的参数组合**
2. **编码问题的解决方案**
3. **大文件处理的最佳实践**
4. **与其他工具的集成方式**
