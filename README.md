# woshipm-crawler

人人都是产品经理 (woshipm.com) 文章爬虫 CatPaw Skill。基于 RSS Feed 获取完整文章数据，支持 9 个分类和全站爬取。

## 安装

```bash
cd ~/.catpaw/skills/
git clone https://github.com/zzzzz9999/woshipm-crawler.git
```

然后在 CatPaw 中说"爬取人人都是产品经理"即可触发。

## 手动使用

```bash
pip install requests beautifulsoup4
python ~/.catpaw/skills/woshipm-crawler/scripts/crawl_woshipm.py
```

默认爬取 AI 分类前 5 页（75 篇），输出 JSON + CSV 到当前目录。

## 获取字段

标题、链接、文章 ID、作者名、发布时间、主分类、标签、摘要、完整正文（HTML + 纯文本）、正文字数、图片 URL、评论数。阅读数需补充爬详情页。

## 支持的分类

`ai`、`pd`、`it`、`zhichang`、`marketing`、`data-analysis`、`evaluating`、`operate`、`user-research`，传 `None` 为全站。

## 技术方案

网站使用 Vue.js 前端渲染，列表页 HTML 中作者/标签由 JS 动态填充，纯 HTTP 爬虫拿不到。RSS Feed 是 WordPress 原生接口，服务端渲染，一次请求 15 篇完整文章，支持 `?paged=N` 分页，全站最多约 29 页（435+ 篇）。

## 目录结构

```
woshipm-crawler/
  SKILL.md                  # CatPaw agent 指令文件
  README.md                 # 本文件
  scripts/
    crawl_woshipm.py        # 爬虫脚本
```

## License

MIT
