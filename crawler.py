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


def generate_markdown(papers: List[Dict]):
    """生成Markdown文件用于GitHub Pages"""
    os.makedirs("docs", exist_ok=True)
    
    md_content = """---
layout: default
title: AI Testing Papers
---

# AI Testing Papers Collection

> 自动从arXiv爬取的AI测试相关论文，每日更新

最后更新: {date}

共收录: **{count}** 篇论文

---

## 论文列表

""".format(
        date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        count=len(papers)
    )
    
    for i, paper in enumerate(papers, 1):
        md_content += f"""
### {i}. {paper['title']}

- **arXiv ID**: [{paper['id']}]({paper['arxiv_url']})
- **PDF**: [下载]({paper['pdf_url']})
- **发布日期**: {paper['published']}
- **作者**: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}
- **分类**: {', '.join(paper['categories'][:3])}

{paper['summary'][:300]}...

---

"""
    
    with open("docs/index.md", "w", encoding="utf-8") as f:
        f.write(md_content)
    
    print(f"Markdown文件已生成到 docs/index.md")


def main():
    print("=" * 60)
    print("AI Testing Papers Crawler")
    print("=" * 60)
    
    papers = search_papers()
    
    if papers:
        save_papers(papers)
        generate_markdown(papers)
        print("\n爬取完成！")
    else:
        print("\n未找到任何论文")


if __name__ == "__main__":
    main()
