# -*- coding: utf-8 -*-
"""
人人都是产品经理 (woshipm.com) 完整文章爬虫
基于 RSS Feed 获取完整文章数据（标题、作者、时间、分类、标签、摘要、正文）

技术要点：
- 网站使用 Vue.js 前端渲染，列表页 HTML 中作者/标签由 JS 动态填充
- RSS Feed 是 WordPress 原生接口，服务端渲染，包含完整文章数据
- 一次请求获取 15 篇完整文章，支持 ?paged=N 分页
- 全站最多约 29 页（435+ 篇），分类分页数取决于文章量

依赖：pip install requests beautifulsoup4
"""
import requests
import xml.etree.ElementTree as ET
import json
import time
import random
import csv
import re
import sys
import os
from html import unescape
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# RSS 命名空间
NS = {
    'dc': 'http://purl.org/dc/elements/1.1/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'slash': 'http://purl.org/rss/1.0/modules/slash/',
    'wfw': 'http://wellformedweb.org/CommentAPI/',
}

CATEGORIES = {
    'ai': 'AI',
    'pd': '产品设计',
    'it': '业界动态',
    'zhichang': '职场攻略',
    'marketing': '营销推广',
    'data-analysis': '数据分析',
    'evaluating': '分析评测',
    'operate': '产品运营',
    'user-research': '用户研究',
}


def strip_html(html_text):
    """去除HTML标签，返回纯文本"""
    if not html_text:
        return ''
    text = re.sub(r'<(?:p|br|/p|/div)[^>]*>', '\n', html_text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', '', text)
    text = unescape(text)
    lines = [line.strip() for line in text.split('\n')]
    lines = [line for line in lines if line]
    return '\n'.join(lines)


def extract_images_from_html(html_text):
    """从HTML中提取图片URL"""
    if not html_text:
        return []
    imgs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_text, re.IGNORECASE)
    return [img for img in imgs if img and not img.startswith('data:')]


def extract_article_id(url):
    """从URL中提取文章ID"""
    m = re.search(r'/(\d+)\.html', url)
    return m.group(1) if m else ''


def parse_rss_item(item):
    """解析单个RSS item，返回结构化文章数据"""
    article = {}

    title_el = item.find('title')
    article['title'] = title_el.text.strip() if title_el is not None and title_el.text else ''

    link_el = item.find('link')
    article['url'] = link_el.text.strip() if link_el is not None and link_el.text else ''

    article['id'] = extract_article_id(article['url'])

    # 作者 (dc:creator)
    creator_el = item.find('dc:creator', NS)
    article['author'] = creator_el.text.strip() if creator_el is not None and creator_el.text else ''

    # 发布时间 (pubDate)
    pubdate_el = item.find('pubDate')
    if pubdate_el is not None and pubdate_el.text:
        raw_date = pubdate_el.text.strip()
        article['publish_date_raw'] = raw_date
        try:
            dt = datetime.strptime(raw_date, '%a, %d %b %Y %H:%M:%S %z')
            article['publish_date'] = dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            article['publish_date'] = raw_date

    # 分类和标签 (category - 多个，第一个为主分类，其余为标签)
    categories = []
    for cat_el in item.findall('category'):
        if cat_el.text:
            categories.append(cat_el.text.strip())
    if categories:
        article['categories'] = categories
        article['main_category'] = categories[0]
        article['tags'] = categories[1:] if len(categories) > 1 else []

    # 摘要 (description - HTML格式)
    desc_el = item.find('description')
    if desc_el is not None and desc_el.text:
        article['summary_html'] = desc_el.text.strip()
        article['summary'] = strip_html(desc_el.text.strip())[:500]

    # 完整正文 (content:encoded - HTML格式)
    encoded_el = item.find('content:encoded', NS)
    if encoded_el is not None and encoded_el.text:
        article['content_html'] = encoded_el.text.strip()
        article['content'] = strip_html(encoded_el.text.strip())
        article['content_length'] = len(article['content'])
        article['images'] = extract_images_from_html(encoded_el.text.strip())

    # 评论数 (slash:comments)
    comments_el = item.find('slash:comments', NS)
    if comments_el is not None and comments_el.text:
        article['comments_count'] = int(comments_el.text.strip())

    # 评论RSS链接 (wfw:commentRss)
    comment_rss_el = item.find('wfw:commentRss', NS)
    if comment_rss_el is not None and comment_rss_el.text:
        article['comment_rss'] = comment_rss_el.text.strip()

    # GUID
    guid_el = item.find('guid')
    if guid_el is not None and guid_el.text:
        article['guid'] = guid_el.text.strip()

    return article


def crawl_rss_feed(category=None, max_pages=5):
    """
    通过RSS feed爬取文章列表

    Args:
        category: None=全站, 'ai'/'pd'/'it'/...=指定分类
        max_pages: 最大翻页数，每页15篇

    Returns:
        list[dict]: 文章列表，每篇包含完整字段
    """
    all_articles = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        if category:
            url = f'https://www.woshipm.com/category/{category}/feed?paged={page}'
            cat_label = CATEGORIES.get(category, category)
        else:
            url = f'https://www.woshipm.com/feed?paged={page}'
            cat_label = '全站'

        print(f"  [{cat_label}] 第 {page}/{max_pages} 页... ", end='', flush=True)

        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code != 200:
                print(f"HTTP {resp.status_code}，停止")
                break

            root = ET.fromstring(resp.text)
            channel = root.find('channel')
            if channel is None:
                print("无channel，停止")
                break

            items = channel.findall('item')
            if not items:
                print("无文章，停止")
                break

            page_count = 0
            for item in items:
                article = parse_rss_item(item)
                article_id = article.get('id', '')
                if article_id and article_id in seen_ids:
                    continue
                if article_id:
                    seen_ids.add(article_id)
                all_articles.append(article)
                page_count += 1

            print(f"获取 {page_count} 篇（累计 {len(all_articles)}）")

            if page < max_pages:
                delay = random.uniform(1.5, 3)
                time.sleep(delay)

        except Exception as e:
            print(f"错误: {e}")
            break

    return all_articles


def crawl_article_detail_page(url):
    """
    补充爬取文章详情页，获取互动数据（阅读数、点赞数等）
    注意：详情页也是JS渲染，只能获取部分SSR数据

    Args:
        url: 文章URL

    Returns:
        dict: 包含 views, likes, ld_author 等字段
    """
    try:
        headers = {
            **HEADERS,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Referer': 'https://www.woshipm.com/',
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.encoding = 'utf-8'
        if resp.status_code != 200:
            return {}

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, 'html.parser')
        detail = {}

        # JSON-LD 结构化数据
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                ld = json.loads(script.string)
                if isinstance(ld, dict) and ld.get('@type') == 'Article':
                    detail['ld_author'] = ld.get('author', {}).get('name', '')
                    detail['ld_date'] = ld.get('datePublished', '')
                    detail['ld_description'] = ld.get('description', '')
                    if ld.get('image'):
                        detail['ld_image'] = ld['image'] if isinstance(ld['image'], str) else ld['image'].get('url', '')
                    break
            except (json.JSONDecodeError, AttributeError):
                pass

        # 阅读数
        for el in soup.find_all(class_=lambda x: x and any(k in str(x).lower() for k in ['views', 'read', 'count'])):
            text = el.get_text().strip()
            nums = re.findall(r'[\d,]+', text)
            if nums:
                detail['views'] = nums[0].replace(',', '')
                break

        # 点赞/收藏数
        for el in soup.find_all(class_=lambda x: x and any(k in str(x).lower() for k in ['like', 'fav', 'star', 'zan'])):
            text = el.get_text().strip()
            nums = re.findall(r'[\d,]+', text)
            if nums:
                detail['likes'] = nums[0].replace(',', '')
                break

        return detail

    except Exception:
        return {}


def save_to_csv(articles, filename):
    """保存概览到CSV（Excel兼容，UTF-8-BOM）"""
    if not articles:
        return
    fieldnames = [
        'id', 'title', 'author', 'main_category', 'publish_date',
        'content_length', 'comments_count', 'tags', 'url'
    ]
    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        for a in articles:
            row = a.copy()
            if isinstance(row.get('tags'), list):
                row['tags'] = ', '.join(row['tags'])
            writer.writerow(row)


def save_to_json(articles, filename):
    """保存完整数据到JSON"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)


def print_stats(articles):
    """打印爬取结果统计"""
    print(f"\n{'='*70}")
    print(f"爬取结果统计")
    print(f"{'='*70}")
    print(f"总文章数: {len(articles)}")

    for key in ['title', 'author', 'publish_date', 'main_category', 'tags',
                 'summary', 'content', 'content_length', 'images', 'comments_count']:
        count = sum(1 for a in articles if a.get(key))
        pct = (count / len(articles) * 100) if articles else 0
        print(f"  {key:20s}: {count:4d}/{len(articles)} ({pct:.0f}%)")

    # 作者分布
    authors = {}
    for a in articles:
        author = a.get('author', '')
        if author:
            authors[author] = authors.get(author, 0) + 1
    if authors:
        print(f"\n作者数: {len(authors)}")
        top_authors = sorted(authors.items(), key=lambda x: -x[1])[:10]
        print("Top 10 作者:")
        for author, count in top_authors:
            print(f"  {author}: {count} 篇")

    # 分类分布
    cats = {}
    for a in articles:
        cat = a.get('main_category', '')
        if cat:
            cats[cat] = cats.get(cat, 0) + 1
    if cats:
        print(f"\n分类分布:")
        for cat, count in sorted(cats.items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count} 篇")


def main():
    """主函数 - 可通过修改以下参数自定义爬取"""
    # ========== 配置 ==========
    category = 'ai'       # None=全站, 'ai'/'pd'/'it'/'zhichang'/'marketing'/'data-analysis'/'evaluating'/'operate'/'user-research'
    max_pages = 5         # RSS分页数，每页15篇
    fetch_details = True  # 是否补充爬取详情页互动数据
    detail_limit = 10     # 详情爬取数量限制
    output_dir = '.'      # 输出目录
    # ========================

    cat_label = CATEGORIES.get(category, category) if category else '全站'

    print(f"{'='*70}")
    print(f"人人都是产品经理 (woshipm.com) RSS 爬虫")
    print(f"数据源: RSS Feed | 分类: {cat_label} | 页数: {max_pages}")
    print(f"{'='*70}\n")

    # Step 1: RSS feed 爬取
    print("[Step 1] RSS Feed 爬取...\n")
    articles = crawl_rss_feed(category=category, max_pages=max_pages)

    if not articles:
        print("未爬取到任何数据！")
        return

    # Step 2: 补充详情页互动数据
    if fetch_details and articles:
        print(f"\n[Step 2] 补充爬取前 {detail_limit} 篇详情页互动数据...\n")
        for i, article in enumerate(articles[:detail_limit]):
            url = article.get('url', '')
            if not url:
                continue
            print(f"  [{i+1}/{detail_limit}] {article.get('title', '')[:40]}...", end=' ', flush=True)
            detail = crawl_article_detail_page(url)
            if detail:
                if detail.get('views'):
                    article['views'] = detail['views']
                if detail.get('likes'):
                    article['likes'] = detail['likes']
                print(f"阅读:{detail.get('views', '?')} 点赞:{detail.get('likes', '?')}")
            else:
                print("无额外数据")
            time.sleep(random.uniform(1, 2))

    # Step 3: 保存
    print(f"\n[Step 3] 保存数据...\n")

    json_file = os.path.join(output_dir, 'woshipm_articles_full.json')
    save_to_json(articles, json_file)
    print(f"完整JSON: {json_file}")

    csv_file = os.path.join(output_dir, 'woshipm_articles.csv')
    save_to_csv(articles, csv_file)
    print(f"概览CSV:  {csv_file}")

    # 统计
    print_stats(articles)

    # 预览前5篇
    print(f"\n{'='*70}")
    print("前5篇文章预览:\n")
    for i, a in enumerate(articles[:5], 1):
        print(f"{i}. {a.get('title', '无标题')}")
        print(f"   作者: {a.get('author', '?')}")
        print(f"   时间: {a.get('publish_date', '?')}")
        print(f"   分类: {a.get('main_category', '?')}")
        tags = a.get('tags', [])
        if tags:
            print(f"   标签: {', '.join(tags)}")
        print(f"   字数: {a.get('content_length', '?')}")
        summary = a.get('summary', '')
        if summary:
            print(f"   摘要: {summary[:100]}...")
        imgs = a.get('images', [])
        if imgs:
            print(f"   图片: {len(imgs)} 张")
        print(f"   链接: {a.get('url', '')}")
        print()


if __name__ == '__main__':
    main()
