#!/usr/bin/env python3
"""
Backfill content_type for existing articles using heuristic rules.
Fast (no LLM calls), ~80% accuracy based on title/category patterns.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.supabase_service import SupabaseService

TUTORIAL_KEYWORDS = [
    "tutorial",
    "how to",
    "how-to",
    "step by step",
    "step-by-step",
    "getting started",
    "get started",
    "beginner",
    "learn ",
    "learning",
    "入門",
    "教學",
    "教程",
    "手把手",
    "從零",
    "快速上手",
]
GUIDE_KEYWORDS = [
    "guide",
    "introduction",
    "intro to",
    "overview",
    "explained",
    "understanding",
    "deep dive",
    "best practices",
    "cheat sheet",
    "指南",
    "介紹",
    "概覽",
    "最佳實踐",
]
REFERENCE_KEYWORDS = [
    "reference",
    "documentation",
    "docs",
    "api ",
    "cheatsheet",
    "specification",
    "spec ",
    "changelog",
    "release notes",
    "文件",
    "規格",
    "速查",
]
PROJECT_KEYWORDS = [
    "build ",
    "building ",
    "create ",
    "creating ",
    "implement",
    "open source",
    "open-source",
    "github",
    "release ",
    "launched",
    "實作",
    "開源",
    "發布",
]
NEWS_KEYWORDS = [
    "announces",
    "announced",
    "launches",
    "launched",
    "acquires",
    "acquisition",
    "funding",
    "raises",
    "ipo",
    "partnership",
    "report",
    "survey",
    "study",
    "research",
    "market",
    "宣布",
    "發表",
    "收購",
    "融資",
    "報告",
    "調查",
]


def classify(title: str, category: str) -> str:
    text = (title + " " + (category or "")).lower()

    for kw in TUTORIAL_KEYWORDS:
        if kw in text:
            return "tutorial"
    for kw in GUIDE_KEYWORDS:
        if kw in text:
            return "guide"
    for kw in REFERENCE_KEYWORDS:
        if kw in text:
            return "reference"
    for kw in PROJECT_KEYWORDS:
        if kw in text:
            return "project"
    for kw in NEWS_KEYWORDS:
        if kw in text:
            return "news"

    # Category-based fallback
    cat = (category or "").lower()
    if any(x in cat for x in ["news", "industry", "aggregator", "platform"]):
        return "news"
    if any(x in cat for x in ["official", "documentation", "reference"]):
        return "reference"

    return "news"  # default: most articles are news


def main():
    supabase = SupabaseService()

    # Fetch all articles without content_type
    resp = (
        supabase.client.table("articles")
        .select("id, title, category")
        .is_("content_type", "null")
        .execute()
    )
    articles = resp.data or []
    print(f"需要補充 content_type 的文章：{len(articles)} 篇")

    if not articles:
        print("沒有需要處理的文章")
        return

    # Classify and batch update
    type_counts: dict[str, int] = {}
    updates: list[dict] = []

    for article in articles:
        ct = classify(article["title"], article.get("category", ""))
        updates.append({"id": article["id"], "content_type": ct})
        type_counts[ct] = type_counts.get(ct, 0) + 1

    # Update in batches of 100
    batch_size = 100
    updated = 0
    for i in range(0, len(updates), batch_size):
        batch = updates[i : i + batch_size]
        supabase.client.table("articles").upsert(batch).execute()
        updated += len(batch)
        print(f"  已更新 {updated}/{len(updates)}...")

    print("\n完成！分類結果：")
    for ct, count in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {ct:12s}: {count} 篇")


if __name__ == "__main__":
    main()
