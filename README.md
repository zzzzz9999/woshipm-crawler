# woshipm-crawler

人人都是产品经理 (woshipm.com) 文章爬虫，基于 RSS Feed 获取完整文章数据。

## 为什么用 RSS 而不是 HTML 爬取？

这个网站使用 Vue.js 前端渲染，列表页 HTML 中作者、标签等字段由 JS 动态填充，纯 HTTP 爬虫拿不到。RSS Feed 是 WordPress 原生接口，服务端渲染，一次请求就能拿到 15 篇文章的全部字段。

三种方案对比：

| 方案 | 能拿到的字段 | 问题 |
|------|-------------|------|
| HTML 列表页 | 标题、链接 | 作者/标签为空（JS 渲染） |
| HTML 详情页 | 正文、时间 | 每篇单独请求，效率低 |
| **RSS Feed** | **全部字段** | 每页仅 15 篇 |

## 获取字段

标题、链接、文章 ID、作者名、发布时间、主分类、标签（多个）、摘要、完整正文（HTML + 纯文本）、正文字数、图片 URL 列表、评论数。阅读数需要补充爬详情页。

## 快速开始

```bash
pip install requests beautifulsoup4
python crawl_woshipm.py
```

默认爬取 AI 分类前 5 页（75 篇），输出 JSON + CSV。

### 作为模块使用

```python
from crawl_woshipm import crawl_rss_feed, save_to_csv, save_to_json

# 爬取 AI 分类前 5 页
articles = crawl_rss_feed(category='ai', max_pages=5)

# 爬取全站最新文章
articles = crawl_rss_feed(category=None, max_pages=3)

# 保存
save_to_json(articles, 'articles.json')
save_to_csv(articles, 'articles.csv')
```

### 支持的分类

`ai`（AI）、`pd`（产品设计）、`it`（业界动态）、`zhichang`（职场攻略）、`marketing`（营销推广）、`data-analysis`（数据分析）、`evaluating`（分析评测）、`operate`（产品运营）、`user-research`（用户研究）。传 `None` 为全站。

## 输出示例

```json
{
  "title": "关于AI、小红书和赚钱，我的45条思考！",
  "url": "https://www.woshipm.com/ai/6431497.html",
  "id": "6431497",
  "author": "林卿LinQ.",
  "publish_date": "2026-07-17 07:12:15",
  "main_category": "AI",
  "tags": ["个人随笔", "AI应用", "个人观点"],
  "summary": "翻遍近一年朋友圈...",
  "content": "这几天把自己最近一年的朋友圈翻了一遍...",
  "content_length": 7162,
  "images": ["https://image.woshipm.com/xxx.jpg"],
  "comments_count": 0
}
```

## 分页能力

每页固定 15 篇，全站最多约 29 页（435+ 篇），通过 `?paged=N` 翻页。

## 技术栈

Python + requests + xml.etree.ElementTree（RSS 解析）+ BeautifulSoup（详情页补充）

## 注意事项

请遵守网站使用条款，控制爬取频率，数据仅供学习研究使用。

## License

MIT
