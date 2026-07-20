---
name: woshipm-crawler
description: 人人都是产品经理 (woshipm.com) 文章爬虫。基于 RSS Feed 获取完整文章数据，支持9个分类和全站爬取，输出JSON/CSV。
metadata:
  version: 1.0.0
  author: zzzzz9999
  tags: [crawler, woshipm, rss, web-scraping, python]
---

# 人人都是产品经理爬虫 (woshipm-crawler)

## 功能

从人人都是产品经理网站爬取文章数据，获取每篇文章的完整信息：

- **标题、链接、文章ID**
- **作者名**（如"林卿LinQ."、"AI星球"）
- **发布时间**（精确到秒）
- **分类和标签**（多个标签）
- **摘要**（纯文本）
- **完整正文**（HTML原文 + 纯文本）
- **正文图片URL列表**
- **评论数**
- **阅读数**（需补充爬详情页）

## 技术方案

### 为什么用 RSS Feed 而不是 HTML 爬取？

人人都是产品经理网站使用 **Vue.js 前端渲染**，分类列表页返回的 HTML 只有骨架结构，作者名、标签文本等由 JavaScript 在浏览器端动态填充。纯 HTTP 爬虫（requests + BeautifulSoup）无法获取这些字段。

尝试了三种方案后，RSS Feed 是最优解：

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| HTTP + BeautifulSoup 解析列表页 | 简单快速 | 作者/标签为空（JS渲染） | 数据不完整 |
| HTTP + BeautifulSoup 解析详情页 | 可获取正文/时间 | 每篇单独请求，效率低 | 适合补充互动数据 |
| **RSS Feed（最终方案）** | 一次请求15篇完整文章，所有字段齐全 | 每页仅15篇 | **最优方案** |

### RSS Feed 端点

```
# 全站
https://www.woshipm.com/feed?paged={page}

# 指定分类
https://www.woshipm.com/category/{category}/feed?paged={page}
```

### 支持的分类

| slug | 名称 |
|------|------|
| ai | AI |
| pd | 产品设计 |
| it | 业界动态 |
| zhichang | 职场攻略 |
| marketing | 营销推广 |
| data-analysis | 数据分析 |
| evaluating | 分析评测 |
| operate | 产品运营 |
| user-research | 用户研究 |

### RSS 字段映射

| RSS 字段 | 提取字段 | 说明 |
|----------|----------|------|
| `title` | 标题 | |
| `link` | 文章URL | |
| `dc:creator` | 作者名 | |
| `pubDate` | 发布时间 | RFC 822 格式 |
| `category` (多个) | 分类+标签 | 第一个为主分类，其余为标签 |
| `description` | 摘要 | HTML 格式 |
| `content:encoded` | 完整正文 | HTML 格式，含图片 |
| `slash:comments` | 评论数 | |
| `wfw:commentRss` | 评论RSS | |

### 分页能力

- 每页固定返回 **15 篇**文章
- 全站 feed 最多可翻 **29 页**（约 435 篇）
- 分类 feed 分页数取决于该分类文章量
- 通过 `?paged=N` 参数翻页

## 使用方法

### 环境要求

```bash
pip install requests beautifulsoup4
```

### 快速开始

```python
from crawl_woshipm import crawl_rss_feed, save_to_csv
import json

# 爬取 AI 分类前 5 页（75篇）
articles = crawl_rss_feed(category='ai', max_pages=5)

# 保存
with open('articles.json', 'w', encoding='utf-8') as f:
    json.dump(articles, f, ensure_ascii=False, indent=2)
save_to_csv(articles, 'articles.csv')
```

### 命令行运行

```bash
python crawl_woshipm.py
```

### 自定义参数

```python
# 爬取全站最新文章
articles = crawl_rss_feed(category=None, max_pages=3)

# 爬取产品设计分类
articles = crawl_rss_feed(category='pd', max_pages=10)

# 补充爬取详情页互动数据（阅读数等）
from crawl_woshipm import crawl_article_detail_page
detail = crawl_article_detail_page(article['url'])
```

## 输出格式

### JSON（完整数据）

```json
{
  "title": "关于AI、小红书和赚钱，我的45条思考！",
  "url": "https://www.woshipm.com/ai/6431497.html",
  "id": "6431497",
  "author": "林卿LinQ.",
  "publish_date": "2026-07-17 07:12:15",
  "main_category": "AI",
  "tags": ["个人随笔", "AI应用", "个人观点", "内容创作", "小红书", "电商", "经验总结"],
  "summary": "翻遍近一年朋友圈，从AI提效的真实边界到...",
  "content": "这几天把自己最近一年的朋友圈翻了一遍...",
  "content_html": "<blockquote><p>翻遍近一年朋友圈...</p></blockquote>...",
  "content_length": 7162,
  "images": ["https://image.woshipm.com/2023/04/14/xxx.jpg"],
  "comments_count": 0
}
```

### CSV（概览）

包含字段：id, title, author, main_category, publish_date, content_length, comments_count, tags, url

## 反爬策略

- 请求间隔 1.5~4 秒随机延迟
- 标准浏览器 User-Agent
- RSS Feed 本身是公开接口，无严格反爬限制

## 注意事项

1. 请遵守网站的 robots.txt 和使用条款
2. 建议控制爬取频率，避免对服务器造成压力
3. 阅读数等互动数据需要额外爬取详情页（JS渲染，只能拿到部分）
4. 数据仅供学习研究使用
