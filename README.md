# woshipm-crawler

A universal [Agent Skill](https://agentskills.io) that crawls full article data from [woshipm.com](https://www.woshipm.com) (人人都是产品经理) via RSS Feed.

Compatible with any agent that supports the [Agent Skills open standard](https://agentskills.io/specification): **Claude Code, Cursor, OpenAI Codex, Cline, GitHub Copilot, Gemini CLI, CatPaw** and others.

## What It Does

Extracts complete article data: title, author, publish date, category, tags, summary, full content (HTML + plain text), image URLs, and comment count. Supports 9 categories and site-wide crawling. Outputs JSON and CSV.

## Install

Clone into your agent's skills directory. The exact path depends on your agent:

| Agent | Skills directory |
|-------|------------------|
| Claude Code | `~/.claude/skills/` or `.claude/skills/` |
| Cursor | `.agents/skills/` or `.cursor/skills/` |
| OpenAI Codex | `.codex/skills/` |
| Cline | `~/.cline/skills/` or `.cline/skills/` |
| CatPaw | `~/.catpaw/skills/` |
| Generic / neutral | `.agents/skills/` |

```bash
cd <your-agent-skills-dir>
git clone https://github.com/zzzzz9999/woshipm-crawler.git
```

Then just ask your agent to "crawl woshipm.com" or "爬取人人都是产品经理" — the agent will discover and run the skill automatically.

## Manual / Standalone Use

The crawler works as a plain Python script, no agent required:

```bash
pip install requests beautifulsoup4
python scripts/crawl_woshipm.py
```

Default: crawls AI category, 5 pages (75 articles), outputs JSON + CSV to current directory.

### As a module

```python
from scripts.crawl_woshipm import crawl_rss_feed, save_to_json, save_to_csv

articles = crawl_rss_feed(category='ai', max_pages=5)   # AI category
articles = crawl_rss_feed(category=None, max_pages=3)   # site-wide
articles = crawl_rss_feed(category='pd', max_pages=10)  # product design

save_to_json(articles, 'articles.json')
save_to_csv(articles, 'articles.csv')
```

## Extracted Fields

title, url, id, author, publish_date, main_category, tags, summary, content (plain text), content_html, content_length, images, comments_count, views (optional).

## Categories

`ai`, `pd` (产品设计), `it` (业界动态), `zhichang` (职场攻略), `marketing` (营销推广), `data-analysis` (数据分析), `evaluating` (分析评测), `operate` (产品运营), `user-research` (用户研究). Pass `None` for site-wide.

## Why RSS Instead of HTML Scraping

The site uses Vue.js client-side rendering — list page HTML only has skeleton structure, with author/tag text populated by JavaScript in the browser. Plain HTTP scraping gets empty fields. RSS Feed is WordPress's native server-side-rendered API, returning 15 complete articles per request with all fields populated. Supports `?paged=N` pagination, ~29 pages max site-wide (435+ articles).

## Structure

```
woshipm-crawler/
├── SKILL.md               # Agent Skills standard instruction file
├── README.md              # This file
└── scripts/
    └── crawl_woshipm.py   # Crawler (also usable standalone)
```

## Tech Stack

Python + requests + xml.etree.ElementTree (RSS parsing) + BeautifulSoup (detail page fallback).

## Notes

Respect the site's terms of service and control crawl frequency. Data is for learning and research purposes only.

## License

MIT
