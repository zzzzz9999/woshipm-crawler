---
name: woshipm-crawler
description: 人人都是产品经理 (woshipm.com) 文章爬虫。基于 RSS Feed 获取完整文章数据（标题、作者、时间、分类、标签、摘要、正文、图片、评论数），支持9个分类和全站爬取，输出JSON/CSV。当用户提到"爬取人人都是产品经理"、"woshipm爬虫"、"产品经理文章爬取"时触发。
metadata:
  version: 1.0.0
  author: zzzzz9999
  tags: [crawler, woshipm, rss, web-scraping, python]
---

# 人人都是产品经理爬虫

## 功能

从 woshipm.com 爬取文章完整数据：标题、作者、发布时间、分类、标签、摘要、完整正文（HTML+纯文本）、图片URL、评论数。

## 技术方案

网站使用 Vue.js 前端渲染，列表页 HTML 中作者/标签由 JS 动态填充，纯 HTTP 爬虫拿不到。RSS Feed 是 WordPress 原生接口，服务端渲染，一次请求 15 篇完整文章。

RSS 端点：
- 全站：`https://www.woshipm.com/feed?paged={page}`
- 分类：`https://www.woshipm.com/category/{category}/feed?paged={page}`

每页 15 篇，全站最多约 29 页（435+ 篇）。

## 使用方法

### Step 1: 确认依赖

```bash
pip install requests beautifulsoup4
```

### Step 2: 运行爬虫

脚本路径：`~/.catpaw/skills/woshipm-crawler/scripts/crawl_woshipm.py`

```bash
python ~/.catpaw/skills/woshipm-crawler/scripts/crawl_woshipm.py
```

默认爬取 AI 分类前 5 页（75 篇），输出到当前目录的 `woshipm_articles_full.json` 和 `woshipm_articles.csv`。

### Step 3: 自定义参数

直接修改脚本中 `main()` 函数的配置区：

```python
category = 'ai'       # 分类，None=全站
max_pages = 5         # 页数，每页15篇
fetch_details = True  # 是否补充详情页互动数据
detail_limit = 10     # 详情爬取数量
output_dir = '.'      # 输出目录
```

或者作为模块导入：

```python
import sys
sys.path.insert(0, '~/.catpaw/skills/woshipm-crawler/scripts')
from crawl_woshipm import crawl_rss_feed, save_to_csv, save_to_json

# 爬取全站最新文章
articles = crawl_rss_feed(category=None, max_pages=3)
save_to_json(articles, 'articles.json')
save_to_csv(articles, 'articles.csv')

# 爬取指定分类
articles = crawl_rss_feed(category='pd', max_pages=10)
```

### 支持的分类

`ai`（AI）、`pd`（产品设计）、`it`（业界动态）、`zhichang`（职场攻略）、`marketing`（营销推广）、`data-analysis`（数据分析）、`evaluating`（分析评测）、`operate`（产品运营）、`user-research`（用户研究）。传 `None` 为全站。

## 输出格式

### JSON 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 文章标题 |
| url | string | 文章链接 |
| id | string | 文章ID |
| author | string | 作者名 |
| publish_date | string | 发布时间 (YYYY-MM-DD HH:MM:SS) |
| main_category | string | 主分类 |
| tags | list[string] | 标签列表 |
| summary | string | 摘要（纯文本） |
| content | string | 完整正文（纯文本） |
| content_html | string | 完整正文（HTML原文） |
| content_length | int | 正文字数 |
| images | list[string] | 正文图片URL列表 |
| comments_count | int | 评论数 |
| views | string | 阅读数（需补充爬详情页） |

### CSV 字段

id, title, author, main_category, publish_date, content_length, comments_count, tags, url

## 结果呈现

爬取完成后，向用户展示：
1. 总文章数和字段覆盖率统计
2. 前 5 篇文章的标题、作者、时间、标签预览
3. 输出文件路径

## 注意事项

- 请求间隔 1.5~4 秒随机延迟，避免对服务器造成压力
- RSS Feed 是公开接口，无严格反爬限制
- 阅读数等互动数据需额外爬详情页（JS 渲染，只能拿到部分）
- 数据仅供学习研究使用
