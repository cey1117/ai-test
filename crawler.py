#!/usr/bin/env python3
"""
AI Testing Papers Crawler
从arXiv爬取AI测试相关的论文
"""

import arxiv
import json
import os
from datetime import datetime
from typing import List, Dict

SEARCH_QUERY = """
(
    cat:cs.AI OR cat:cs.LG OR cat:cs.SE OR cat:cs.CL
)
AND (
    ti:"AI testing" OR
    ti:"testing AI" OR
    ti:"machine learning testing" OR
    ti:"deep learning testing" OR
    ti:"neural network testing" OR
    ti:"test AI" OR
    ti:"AI verification" OR
    ti:"AI validation" OR
    ti:"metamorphic testing" OR
    ti:"fuzzing neural" OR
    ti:"adversarial testing" OR
    ti:"model testing" OR
    ti:"LLM testing" OR
    ti:"large language model testing" OR
    abs:"AI testing" OR
    abs:"machine learning testing" OR
    abs:"deep learning testing"
)
"""

MAX_RESULTS = 100
OUTPUT_DIR = "data"
PAPERS_FILE = os.path.join(OUTPUT_DIR, "papers.json")


def search_papers() -> List[Dict]:
    """从arXiv搜索AI测试相关论文"""
    print(f"开始搜索arXiv论文...")
    print(f"搜索关键词: AI Testing相关")
    
    search = arxiv.Search(
        query=SEARCH_QUERY,
        max_results=MAX_RESULTS,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )
    
    papers = []
    for result in search.results():
        paper = {
            "id": result.entry_id.split("/")[-1],
            "title": result.title,
            "authors": [author.name for author in result.authors],
            "summary": result.summary.replace("\n", " ").strip(),
            "published": result.published.strftime("%Y-%m-%d"),
            "updated": result.updated.strftime("%Y-%m-%d"),
            "pdf_url": result.pdf_url,
            "arxiv_url": result.entry_id,
            "categories": result.categories,
            "primary_category": result.primary_category
        }
        papers.append(paper)
        print(f"  找到: {paper['title'][:60]}...")
    
    print(f"\n总共找到 {len(papers)} 篇论文")
    return papers


def save_papers(papers: List[Dict]):
    """保存论文数据到JSON文件"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    data = {
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_papers": len(papers),
        "papers": papers
    }
    
    with open(PAPERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"论文数据已保存到 {PAPERS_FILE}")


def generate_html(papers: List[Dict]):
    """生成静态HTML文件用于GitHub Pages (博客风格)"""
    today = datetime.now().strftime("%Y-%m-%d")
    today_dir = os.path.join("docs", today)
    os.makedirs(today_dir, exist_ok=True)
    
    paper_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Testing Papers - {date}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.8; color: #333; background: #fff; }
        header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 60px 20px; text-align: center; }
        header h1 { font-size: 2.5em; margin-bottom: 10px; }
        header .subtitle { opacity: 0.9; font-size: 1.1em; }
        header .meta { margin-top: 20px; opacity: 0.8; font-size: 0.9em; }
        .container { max-width: 900px; margin: 0 auto; padding: 40px 20px; }
        .nav-links { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
        .nav-links a { color: #667eea; text-decoration: none; margin: 0 15px; }
        .nav-links a:hover { text-decoration: underline; }
        .paper-list { list-style: none; }
        .paper-item { padding: 30px; margin-bottom: 25px; border-radius: 8px; border: 1px solid #eee; transition: all 0.3s ease; }
        .paper-item:hover { box-shadow: 0 5px 20px rgba(0,0,0,0.08); border-color: #ddd; }
        .paper-title { font-size: 1.3em; color: #2d3748; margin-bottom: 15px; }
        .paper-title a { color: #667eea; text-decoration: none; }
        .paper-title a:hover { text-decoration: underline; }
        .paper-meta { font-size: 0.95em; color: #718096; margin-bottom: 12px; }
        .paper-meta span { margin-right: 20px; }
        .paper-meta strong { color: #4a5568; }
        .paper-summary { color: #4a5568; font-size: 1em; line-height: 1.8; }
        .tag { display: inline-block; background: #ebf8ff; color: #3182ce; padding: 4px 10px; border-radius: 4px; font-size: 0.8em; margin-right: 8px; margin-top: 5px; }
        footer { background: #2d3748; color: #a0aec0; padding: 40px 20px; text-align: center; margin-top: 60px; }
        footer a { color: #667eea; text-decoration: none; }
        footer a:hover { text-decoration: underline; }
        .count-badge { background: #667eea; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; }
    </style>
</head>
<body>
    <header>
        <h1>AI Testing Papers</h1>
        <p class="subtitle">自动从arXiv爬取的AI测试相关论文</p>
        <div class="meta">
            <span>📅 更新日期: {date}</span>
            <span style="margin: 0 10px;">|</span>
            <span class="count-badge">共 {count} 篇论文</span>
        </div>
    </header>
    
    <div class="container">
        <div class="nav-links">
            <a href="/ai-test/">🏠 首页</a>
            <a href="/ai-test/{date}/papers">📄 今日论文</a>
        </div>
        
        <h2 style="color: #2d3748; margin-bottom: 25px; font-size: 1.5em;">📚 论文列表</h2>
        
        <div class="paper-list">
""".format(
        date=today,
        count=len(papers)
    )
    
    for i, paper in enumerate(papers, 1):
        paper_html += f"""
            <div class="paper-item">
                <h3 class="paper-title"><a href="{paper['arxiv_url']}" target="_blank" rel="noopener">{i}. {paper['title']}</a></h3>
                <div class="paper-meta">
                    <span><strong>arXiv ID:</strong> <a href="{paper['arxiv_url']}" target="_blank" rel="noopener">{paper['id']}</a></span>
                    <span><strong>PDF:</strong> <a href="{paper['pdf_url']}" target="_blank" rel="noopener">📥 下载</a></span>
                    <span><strong>发布:</strong> {paper['published']}</span>
                </div>
                <div class="paper-meta">
                    <span><strong>作者:</strong> {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <strong style="color: #4a5568;">分类:</strong>
                    {''.join(f'<span class="tag">{cat}</span>' for cat in paper['categories'][:3])}
                </div>
                <p class="paper-summary">{paper['summary'][:350]}...</p>
            </div>
"""
    
    paper_html += """
        </div>
    </div>
    
    <footer>
        <p>数据来源: <a href="https://arxiv.org" target="_blank">arXiv</a> | 自动更新</p>
        <p style="margin-top: 10px; font-size: 0.9em;">AI Testing Papers Collection</p>
    </footer>
</body>
</html>"""
    
    with open(os.path.join(today_dir, "papers.html"), "w", encoding="utf-8") as f:
        f.write(paper_html)
    
    generate_index(papers, today)
    print(f"HTML文件已生成到 {today_dir}/papers.html")


def generate_index(papers: List[Dict], today: str):
    """生成首页索引"""
    index_html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Testing Papers Collection</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.8; color: #333; background: #f7fafc; }
        header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 80px 20px; text-align: center; }
        header h1 { font-size: 3em; margin-bottom: 15px; }
        header .subtitle { opacity: 0.9; font-size: 1.2em; }
        header .meta { margin-top: 25px; opacity: 0.85; font-size: 1em; }
        .container { max-width: 800px; margin: 0 auto; padding: 50px 20px; }
        .stats { display: flex; justify-content: center; gap: 40px; margin-bottom: 50px; }
        .stat-item { text-align: center; }
        .stat-value { font-size: 2.5em; font-weight: bold; color: #667eea; }
        .stat-label { color: #718096; font-size: 0.95em; margin-top: 5px; }
        .section { background: white; padding: 35px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; }
        .section-title { font-size: 1.4em; color: #2d3748; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #667eea; }
        .latest-papers { list-style: none; }
        .latest-item { padding: 20px; border-bottom: 1px solid #eee; transition: background 0.2s; }
        .latest-item:last-child { border-bottom: none; }
        .latest-item:hover { background: #f7fafc; }
        .latest-title { font-size: 1.1em; color: #2d3748; margin-bottom: 8px; }
        .latest-title a { color: #667eea; text-decoration: none; }
        .latest-title a:hover { text-decoration: underline; }
        .latest-meta { font-size: 0.9em; color: #718096; }
        .archive-list { list-style: none; }
        .archive-item { padding: 15px 20px; background: #f7fafc; border-radius: 8px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
        .archive-item:hover { background: #edf2f7; }
        .archive-link { color: #667eea; text-decoration: none; font-size: 1.1em; }
        .archive-link:hover { text-decoration: underline; }
        .archive-count { background: #667eea; color: white; padding: 3px 10px; border-radius: 20px; font-size: 0.85em; }
        footer { background: #2d3748; color: #a0aec0; padding: 40px 20px; text-align: center; margin-top: 60px; }
        footer a { color: #667eea; text-decoration: none; }
        .btn-primary { display: inline-block; background: #667eea; color: white; padding: 12px 30px; border-radius: 8px; text-decoration: none; font-weight: 500; margin-top: 20px; transition: background 0.3s; }
        .btn-primary:hover { background: #5a6fd6; }
    </style>
</head>
<body>
    <header>
        <h1>AI Testing Papers</h1>
        <p class="subtitle">自动从arXiv爬取的AI测试相关论文集合</p>
        <div class="meta">
            <span>🔄 每日自动更新</span>
        </div>
        <a href="/ai-test/{today}/papers" class="btn-primary">📖 查看今日论文</a>
    </header>
    
    <div class="container">
        <div class="stats">
            <div class="stat-item">
                <div class="stat-value">{count}</div>
                <div class="stat-label">论文数量</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">📅</div>
                <div class="stat-label">每日更新</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">🤖</div>
                <div class="stat-label">AI测试领域</div>
            </div>
        </div>
        
        <div class="section">
            <h2 class="section-title">🔥 最新论文</h2>
            <ul class="latest-papers">
""".format(
        today=today,
        count=len(papers)
    )
    
    for paper in papers[:5]:
        index_html += f"""
                <li class="latest-item">
                    <div class="latest-title"><a href="{paper['arxiv_url']}" target="_blank" rel="noopener">{paper['title']}</a></div>
                    <div class="latest-meta">
                        <span>作者: {', '.join(paper['authors'][:2])}{'...' if len(paper['authors']) > 2 else ''}</span>
                        <span style="margin: 0 10px;">|</span>
                        <span>{paper['published']}</span>
                    </div>
                </li>
"""
    
    index_html += """
            </ul>
        </div>
        
        <div class="section">
            <h2 class="section-title">📚 归档</h2>
            <ul class="archive-list">
                <li class="archive-item">
                    <a href="/ai-test/{today}/papers" class="archive-link">📄 {today} - 今日更新</a>
                    <span class="archive-count">{count} 篇</span>
                </li>
            </ul>
        </div>
    </div>
    
    <footer>
        <p>数据来源: <a href="https://arxiv.org" target="_blank">arXiv</a></p>
        <p style="margin-top: 10px; font-size: 0.9em;">AI Testing Papers Collection</p>
    </footer>
</body>
</html>"""
    
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    
    print(f"首页已生成到 docs/index.html")


def main():
    print("=" * 60)
    print("AI Testing Papers Crawler")
    print("=" * 60)
    
    papers = search_papers()
    
    if papers:
        save_papers(papers)
        generate_html(papers)
        print("\n爬取完成！")
    else:
        print("\n未找到任何论文")


if __name__ == "__main__":
    main()
