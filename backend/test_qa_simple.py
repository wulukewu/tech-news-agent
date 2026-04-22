#!/usr/bin/env python3
"""
簡單的 QA Agent 測試腳本
用於驗證 Simple QA Agent 是否能正常運作
"""

import asyncio
import sys
from uuid import uuid4

# Add backend to path
sys.path.insert(0, "/app")

from app.qa_agent.simple_qa import get_simple_qa_agent


async def test_simple_qa():
    """測試 Simple QA Agent"""

    print("=" * 60)
    print("Simple QA Agent 測試")
    print("=" * 60)

    # 初始化 agent
    agent = get_simple_qa_agent()
    print(f"✓ Agent 初始化成功: {agent.name}")

    # 測試查詢
    test_queries = [
        "AI 技術的最新發展趨勢是什麼？",
        "What are the latest trends in machine learning?",
        "如何學習 Python 程式設計？",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'=' * 60}")
        print(f"測試 {i}: {query}")
        print(f"{'=' * 60}")

        try:
            # 處理查詢
            user_id = uuid4()
            response = await agent.process_query(user_id=user_id, query=query)

            # 顯示結果
            print("\n✓ 查詢處理成功")
            print(f"  - 對話 ID: {response.conversation_id}")
            print(f"  - 回應時間: {response.response_time}s")
            print(f"  - 找到文章數: {len(response.articles)}")

            # 顯示文章
            if response.articles:
                print("\n  文章列表:")
                for j, article in enumerate(response.articles, 1):
                    print(f"    {j}. {article['title']}")
                    print(f"       相關性: {article['relevance_score']:.2f}")
                    print(f"       摘要: {article['summary'][:100]}...")

            # 顯示洞察
            if response.insights:
                print("\n  洞察:")
                for insight in response.insights:
                    print(f"    - {insight}")

            # 顯示建議
            if response.recommendations:
                print("\n  建議:")
                for rec in response.recommendations:
                    print(f"    - {rec}")

        except Exception as e:
            print(f"\n✗ 查詢處理失敗: {e}")
            import traceback

            traceback.print_exc()

    print(f"\n{'=' * 60}")
    print("測試完成")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    asyncio.run(test_simple_qa())
