#!/usr/bin/env python3
"""
微信公众号文章抓取工具
使用 requests + 正则表达式提取文章内容
"""

import sys
import re
import json
import requests
from urllib.parse import urlparse, parse_qs


def fetch_wechat_article(url):
    """抓取微信公众号文章内容"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Referer': 'https://mp.weixin.qq.com/',
    }
    
    try:
        print(f"正在抓取: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"请求失败: {response.status_code}")
            return None
        
        html = response.text
        
        # 提取标题：优先 og:title，回退 rich_media_title
        og_title_match = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]+)"', html)
        if og_title_match:
            title = og_title_match.group(1).strip()
        else:
            title_match = re.search(r'<h1[^>]*class="rich_media_title[^"]*"[^>]*>(.*?)</h1>', html, re.DOTALL)
            title = title_match.group(1).strip() if title_match else "未知标题"
            title = re.sub(r'<[^>]+>', '', title)
        
        # 提取公众号名称：优先 var author，回退 og:article:author，再回退 profile_nickname
        author_match = re.search(r'var\s+author\s*=\s*"([^"]+)"', html)
        if author_match:
            nickname = author_match.group(1).strip()
        else:
            og_author_match = re.search(r'<meta[^>]*property="og:article:author"[^>]*content="([^"]+)"', html)
            if og_author_match:
                nickname = og_author_match.group(1).strip()
            else:
                nickname_match = re.search(r'<span[^>]*class="profile_nickname"[^>]*>(.*?)</span>', html, re.DOTALL)
                nickname = nickname_match.group(1).strip() if nickname_match else "未知公众号"
                nickname = re.sub(r'<[^>]+>', '', nickname)
        
        # 提取发布时间：优先 var createTime，回退 var ct 时间戳，再回退 var s
        ct_match = re.search(r"var\s+createTime\s*=\s*'([^']+)'", html)
        if ct_match:
            publish_time = ct_match.group(1).strip()
        else:
            ct_ts_match = re.search(r'var\s+ct\s*=\s*"?(\d+)"?', html)
            if ct_ts_match:
                try:
                    from datetime import datetime
                    publish_time = datetime.fromtimestamp(int(ct_ts_match.group(1))).strftime('%Y-%m-%d %H:%M')
                except Exception:
                    publish_time = "未知时间"
            else:
                s_match = re.search(r'var s="(\d{4}-\d{2}-\d{2})"', html)
                publish_time = s_match.group(1) if s_match else "未知时间"
        
        # 提取正文内容
        content_match = re.search(r'<div[^>]*class="rich_media_content[^"]*"[^>]*>(.*?)</div>\s*<script', html, re.DOTALL)
        if content_match:
            content_html = content_match.group(1)
            # 简单的 HTML 转文本
            content = html_to_text(content_html)
        else:
            content = "无法提取正文内容"
        
        return {
            'title': title,
            'nickname': nickname,
            'publish_time': publish_time,
            'url': url,
            'content': content
        }
        
    except Exception as e:
        print(f"抓取失败: {e}")
        return None


def html_to_text(html):
    """将 HTML 转换为纯文本"""
    # 移除 script 和 style
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    
    # 替换常见标签
    html = re.sub(r'<br\s*/?>', '\n', html)
    html = re.sub(r'<p[^>]*>', '\n', html)
    html = re.sub(r'</p>', '', html)
    html = re.sub(r'<div[^>]*>', '\n', html)
    html = re.sub(r'</div>', '', html)
    html = re.sub(r'<li[^>]*>', '\n• ', html)
    html = re.sub(r'</li>', '', html)
    
    # 图片标记前后换行
    html = re.sub(r'<img[^>]*>', '\n[图片]\n', html)
    
    # 移除所有 HTML 标签
    text = re.sub(r'<[^>]+>', '', html)
    
    # HTML 实体转义
    text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
    
    # section 编号换行：在"两位数字+空格+≥3连续中文"前加换行（排除正文数字串误伤）
    text = re.sub(r'(?<![\n\d])(\d{2}\s+[\u4e00-\u9fff]{3,})', r'\n\1', text)
    
    # 清理空白
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    
    return text.strip()


def save_to_markdown(article, output_file=None):
    """保存为 Markdown 格式"""
    if output_file is None:
        # 使用标题作为文件名
        safe_title = re.sub(r'[^\w\u4e00-\u9fff]+', '_', article['title'])[:50]
        output_file = f"{safe_title}.md"
    
    md_content = f"""# {article['title']}

> 来源：{article['nickname']}  
> 时间：{article['publish_time']}  
> 链接：{article['url']}

---

{article['content']}

---

*本文内容由工具自动抓取*
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"已保存到: {output_file}")
    return output_file


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python wechat_fetch.py <微信公众号文章URL>")
        print("示例: python wechat_fetch.py https://mp.weixin.qq.com/s/xxxxx")
        sys.exit(1)
    
    url = sys.argv[1]
    article = fetch_wechat_article(url)
    
    if article:
        print(f"\n标题: {article['title']}")
        print(f"公众号: {article['nickname']}")
        print(f"发布时间: {article['publish_time']}")
        print(f"内容长度: {len(article['content'])} 字符")
        
        output_file = save_to_markdown(article)
        
        # 同时输出 JSON
        json_file = output_file.replace('.md', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(article, f, ensure_ascii=False, indent=2)
        print(f"JSON 已保存到: {json_file}")
    else:
        print("抓取失败")
        sys.exit(1)
