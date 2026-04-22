#!/usr/bin/env python3
"""
測試 QA API 的實際回應格式
"""

import asyncio
import sys
from uuid import uuid4

sys.path.insert(0, "/app")

import json

from app.qa_agent.simple_qa import get_simple_qa_agent


async def test_api_response():
    """測試 API 回應格式"""

    print("=" * 60)
    print("測試 QA API 回應格式")
    print("=" * 60)

    # 初始化 agent
    agent = get_simple_qa_agent()

    # 測試查詢
    query = "AI 技術的最新發展趨勢是什麼？"
    user_id = uuid4()

    print(f"\n查詢: {query}")
    print(f"用戶 ID: {user_id}")
    print()

    # 處理查詢
    response = await agent.process_query(user_id=user_id, query=query)

    # 檢查回應結構
    print("=" * 60)
    print("SimpleQAResponse 結構")
    print("=" * 60)
    print(f"類型: {type(response)}")
    print(f"屬性: {dir(response)}")
    print()

    # 顯示各個欄位
    print("=" * 60)
    print("回應內容")
    print("=" * 60)
    print(f"\n1. query: {response.query}")
    print(f"\n2. conversation_id: {response.conversation_id}")
    print(f"\n3. response_time: {response.response_time}")
    print(f"\n4. articles ({len(response.articles)} 篇):")
    for i, article in enumerate(response.articles, 1):
        print(f"\n   文章 {i}:")
        print(f"   - article_id: {article['article_id']}")
        print(f"   - title: {article['title']}")
        print(f"   - summary: {article['summary'][:100]}...")
        print(f"   - url: {article['url']}")
        print(f"   - relevance_score: {article['relevance_score']}")
        print(f"   - reading_time: {article['reading_time']}")
        print(f"   - category: {article.get('category', 'N/A')}")

    print(f"\n5. insights ({len(response.insights)} 個):")
    for i, insight in enumerate(response.insights, 1):
        print(f"   {i}. {insight}")

    print(f"\n6. recommendations ({len(response.recommendations)} 個):")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"   {i}. {rec}")

    print("\n7. metadata:")
    print(f"   {response.metadata}")

    # 模擬 API 回應格式
    print("\n" + "=" * 60)
    print("模擬 API 回應 JSON")
    print("=" * 60)

    api_response = {
        "success": True,
        "data": {
            "query": response.query,
            "articles": [
                {
                    "article_id": article["article_id"],
                    "title": article["title"],
                    "summary": article["summary"],
                    "url": article["url"],
                    "relevance_score": article["relevance_score"],
                    "reading_time": article["reading_time"],
                    "key_insights": [],
                    "published_at": None,
                    "category": article.get("category", "Technology"),
                }
                for article in response.articles
            ],
            "insights": response.insights,
            "recommendations": response.recommendations,
            "conversation_id": response.conversation_id,
            "response_time": response.response_time,
        },
    }

    print(json.dumps(api_response, indent=2, ensure_ascii=False))

    # 驗證格式
    print("\n" + "=" * 60)
    print("格式驗證")
    print("=" * 60)

    checks = [
        ("success 欄位存在", "success" in api_response),
        ("data 欄位存在", "data" in api_response),
        ("query 欄位存在", "query" in api_response["data"]),
        ("articles 是列表", isinstance(api_response["data"]["articles"], list)),
        ("articles 不為空", len(api_response["data"]["articles"]) > 0),
        ("insights 是列表", isinstance(api_response["data"]["insights"], list)),
        ("recommendations 是列表", isinstance(api_response["data"]["recommendations"], list)),
        ("conversation_id 存在", "conversation_id" in api_response["data"]),
        ("response_time 存在", "response_time" in api_response["data"]),
    ]

    all_passed = True
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有檢查通過！API 回應格式正確")
    else:
        print("❌ 有檢查失敗！需要修復")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_api_response())
