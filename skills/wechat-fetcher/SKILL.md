---
name: wechat-fetcher
description: 微信公众号文章抓取与内容提取工具。使用当需要获取公众号文章内容、提取文章正文、保存为 Markdown 格式时使用。支持自动提取标题、公众号名称、发布时间和正文内容。
---

# WeChat Fetcher - 微信公众号文章抓取工具

用于抓取微信公众号文章内容并转换为 Markdown 格式的工具。

## 功能特性

- 抓取公众号文章完整内容
- 自动提取：标题、公众号名称、发布时间、正文
- 保存为 Markdown 格式（易读）
- 保存为 JSON 格式（结构化数据）
- 支持图片标记（显示为 [图片]）

## 使用方法

### 基本用法

```python
# 使用内置脚本抓取文章
python scripts/wechat_fetch.py "https://mp.weixin.qq.com/s/xxxxx"
```

### 在代码中调用

```python
from scripts.wechat_fetch import fetch_wechat_article, save_to_markdown

# 抓取文章
article = fetch_wechat_article("https://mp.weixin.qq.com/s/xxxxx")

# 保存为 Markdown
save_to_markdown(article, "输出文件.md")
```

## 输出格式

### Markdown 输出

```markdown
# 文章标题

> 来源：公众号名称  
> 时间：2024-01-01  
> 链接：https://mp.weixin.qq.com/s/xxxxx

---

正文内容...

---

*本文内容由工具自动抓取*
```

### JSON 输出

```json
{
  "title": "文章标题",
  "nickname": "公众号名称",
  "publish_time": "2024-01-01",
  "url": "https://mp.weixin.qq.com/s/xxxxx",
  "content": "正文内容..."
}
```

## 依赖要求

- Python 3.8+
- requests
- 标准库（re, json, urllib）

## 注意事项

1. 仅用于个人学习研究，请遵守相关法律法规
2. 部分文章可能有访问限制（需要登录）
3. 抓取频率不宜过高，避免对服务器造成压力
4. 图片会被标记为 `[图片]`，不会实际下载

## 故障排除

### 抓取失败

- 检查 URL 是否正确
- 检查网络连接
- 部分文章可能需要微信客户端才能访问

### 内容提取不完整

- 微信公众号页面结构可能变化
- 尝试更新脚本中的正则表达式

## 更新日志

- v1.0.0: 初始版本，支持基本文章抓取
