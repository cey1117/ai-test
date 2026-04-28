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
    """生成静态HTML文件用于GitHub Pages"""
    os.makedirs("docs", exist_ok=True)
    
    html_content = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Testing Papers Collection</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
        header { text-align: center; margin-bottom: 40px; padding-bottom: 20px; border-bottom: 1px solid #eee; }
        h1 { color: #2c3e50; margin-bottom: 10px; }
        .subtitle { color: #7f8c8d; font-size: 1.1em; }
        .meta { color: #95a5a6; font-size: 0.9em; margin-top: 15px; }
        .paper-list { list-style: none; }
        .paper-item { background: white; padding: 25px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .paper-title { font-size: 1.2em; color: #2c3e50; margin-bottom: 15px; }
        .paper-title a { color: #3498db; text-decoration: none; }
        .paper-title a:hover { text-decoration: underline; }
        .paper-meta { font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px; }
        .paper-meta span { margin-right: 15px; }
        .paper-summary { color: #555; font-size: 0.95em; }
        .tag { display: inline-block; background: #e7f5ff; color: #0969da; padding: 3px 8px; border-radius: 4px; font-size: 0.8em; margin-right: 5px; }
        footer { text-align: center; margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #95a5a6; font-size: 0.85em; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>AI Testing Papers Collection</h1>
            <p class="subtitle">自动从arXiv爬取的AI测试相关论文，每日更新</p>
            <div class="meta">
                <span>最后更新: {date}</span>
                <span>|</span>
                <span>共收录: <strong>{count}</strong> 篇论文</span>
            </div>
        </header>
        
        <div class="paper-list">
""".format(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        count=len(papers)
    )
    
    for i, paper in enumerate(papers, 1):
        html_content += f"""
            <div class="paper-item">
                <h2 class="paper-title"><a href="{paper['arxiv_url']}" target="_blank">{i}. {paper['title']}</a></h2>
                <div class="paper-meta">
                    <span><strong>arXiv ID:</strong> <a href="{paper['arxiv_url']}" target="_blank">{paper['id']}</a></span>
                    <span><strong>PDF:</strong> <a href="{paper['pdf_url']}" target="_blank">下载</a></span>
                    <span><strong>发布日期:</strong> {paper['published']}</span>
                </div>
                <div class="paper-meta">
                    <span><strong>作者:</strong> {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}</span>
                </div>
                <div class="paper-meta">
                    <strong>分类:</strong> {''.join(f'<span class="tag">{cat}</span>' for cat in paper['categories'][:3])}
                </div>
                <p class="paper-summary">{paper['summary'][:300]}...</p>
            </div>
"""
    
    html_content += """
        </div>
        
        <footer>
            <p>数据来源: arXiv | 自动更新</p>
        </footer>
    </div>
</body>
</html>"""
    
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"HTML文件已生成到 docs/index.html")


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
