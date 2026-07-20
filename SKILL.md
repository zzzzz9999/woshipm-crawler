---
name: woshipm-crawler
description: Crawl articles from woshipm.com (人人都是产品经理) via RSS Feed. Extracts full article data including title, author, publish date, category, tags, summary, full content (HTML + plain text), images, and comment count. Supports 9 categories and site-wide crawling. Outputs JSON/CSV. Use when the user wants to scrape, crawl, or extract article data from woshipm.com or 人人都是产品经理.
license: MIT
compatibility: Requires Python 3.6+, requests, beautifulsoup4, and network access.
metadata:
  author: zzzzz9999
  version: "1.0.0"
  tags: crawler, woshipm, rss, web-scraping, python
---

# woshipm.com Article Crawler

Crawl full article data from [woshipm.com](https://www.woshipm.com) (人人都是产品经理), a leading Chinese product management community.

## What It Extracts

| Field | Source | Coverage |
|-------|--------|----------|
| Title | RSS `title` | 100% |
| URL | RSS `link` | 100% |
| Article ID | Extracted from URL | 100% |
| Author | RSS `dc:creator` | 100% |
| Publish date | RSS `pubDate` | 100% |
| Main category | RSS `category[0]` | 100% |
| Tags | RSS `category[1:]` | ~95% |
| Summary | RSS `description` | 100% |
| Full content | RSS `content:encoded` | 100% |
| Content length | Computed | 100% |
| Images | Extracted from HTML | 100% |
| Comment count | RSS `slash:comments` | ~72% |
| View count | Detail page (optional) | Partial |

## Why RSS Instead of HTML Scraping

The site uses Vue.js client-side rendering. List page HTML only contains skeleton structure — author names, tag text, etc. are populated by JavaScript in the browser. Plain HTTP scraping (requests + BeautifulSoup) gets empty fields.

RSS Feed is WordPress's native API, server-side rendered, returning 15 complete articles per request with all fields populated.

**RSS endpoints:**

```
# Site-wide
https://www.woshipm.com/feed?paged={page}

# By category
https://www.woshipm.com/category/{category}/feed?paged={page}
```

15 articles per page, ~29 pages max site-wide (435+ articles).

## Usage

### Step 1: Install dependencies

```bash
pip install requests beautifulsoup4
```

### Step 2: Run the crawler

The script is located at `scripts/crawl_woshipm.py` relative to this SKILL.md.

```bash
python scripts/crawl_woshipm.py
```

Default: crawls AI category, 5 pages (75 articles), outputs `woshipm_articles_full.json` and `woshipm_articles.csv` to current directory.

### Step 3: Customize

Edit the config block in `main()`:

```python
category = 'ai'       # Category slug, None for site-wide
max_pages = 5         # Pages to crawl, 15 articles per page
fetch_details = True  # Fetch detail pages for view counts
detail_limit = 10     # How many detail pages to fetch
output_dir = '.'      # Output directory
```

Or import as a module:

```python
from crawl_woshipm import crawl_rss_feed, save_to_csv, save_to_json

# Site-wide latest articles
articles = crawl_rss_feed(category=None, max_pages=3)

# Specific category
articles = crawl_rss_feed(category='pd', max_pages=10)

save_to_json(articles, 'articles.json')
save_to_csv(articles, 'articles.csv')
```

### Available categories

| Slug | Name |
|------|------|
| `ai` | AI |
| `pd` | 产品设计 |
| `it` | 业界动态 |
| `zhichang` | 职场攻略 |
| `marketing` | 营销推广 |
| `data-analysis` | 数据分析 |
| `evaluating` | 分析评测 |
| `operate` | 产品运营 |
| `user-research` | 用户研究 |

Pass `None` for site-wide crawling.

## Output Format

### JSON

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
  "content_html": "<blockquote><p>...</p></blockquote>...",
  "content_length": 7162,
  "images": ["https://image.woshipm.com/xxx.jpg"],
  "comments_count": 0
}
```

### CSV columns

`id, title, author, main_category, publish_date, content_length, comments_count, tags, url`

## Presenting Results

After crawling, show the user:
1. Total article count and field coverage stats
2. Preview of first 5 articles (title, author, date, tags)
3. Output file paths

## Rate Limiting

- 1.5–4 second random delay between requests
- Standard browser User-Agent
- RSS Feed is a public endpoint with no strict anti-scraping

## Notes

- Respect the site's terms of service
- Data is for learning and research purposes only
- View counts require fetching individual detail pages (JS-rendered, partial data)
