#!/usr/bin/env python3
"""
測試完整的 API 端點流程
"""

import asyncio
import sys
from uuid import uuid4

sys.path.insert(0, "/app")

import json

from app.api.qa import ArticleSummaryResponse, QAQueryResponse
from app.qa_agent.simple_qa import get_simple_qa_agent
from app.schemas.responses import success_response


async def test_full_api_flow():
    """測試完整的 API 流程"""

    print("=" * 60)
    print("測試完整 API 流程")
    print("=" * 60)

    # 步驟 1: 呼叫 Simple QA Agent
    print("\n步驟 1: 呼叫 Simple QA Agent")
    print("-" * 60)

    agent = get_simple_qa_agent()
    user_id = uuid4()
    query = "AI 技術的最新發展趨勢是什麼？"

    response = await agent.process_query(user_id=user_id, query=query)

    print("✅ Agent 回應成功")
    print(f"   - 查詢: {response.query}")
    print(f"   - 文章數: {len(response.articles)}")
    print(f"   - 洞察數: {len(response.insights)}")
    print(f"   - 建議數: {len(response.recommendations)}")

    # 步驟 2: 轉換為 QAQueryResponse
    print("\n步驟 2: 轉換為 QAQueryResponse")
    print("-" * 60)

    result = QAQueryResponse(
        query=response.query,
        articles=[
            ArticleSummaryResponse(
                article_id=article["article_id"],
                title=article["title"],
                summary=article["summary"],
                url=article["url"],
                relevance_score=article["relevance_score"],
                reading_time=article["reading_time"],
                key_insights=[],
                published_at=None,
                category=article.get("category", "Technology"),
            )
            for article in response.articles
        ],
        insights=response.insights,
        recommendations=response.recommendations,
        conversation_id=response.conversation_id,
        response_time=response.response_time,
    )

    print("✅ 轉換成功")
    print(f"   - 類型: {type(result)}")
    print(f"   - 文章數: {len(result.articles)}")

    # 步驟 3: 包裝為 SuccessResponse
    print("\n步驟 3: 包裝為 SuccessResponse")
    print("-" * 60)

    api_response = success_response(result)

    print("✅ 包裝成功")
    print(f"   - 類型: {type(api_response)}")
    print(f"   - success: {api_response.success}")
    print(f"   - data 類型: {type(api_response.data)}")

    # 步驟 4: 序列化為 JSON
    print("\n步驟 4: 序列化為 JSON")
    print("-" * 60)

    try:
        # 使用 Pydantic 的 model_dump
        json_dict = api_response.model_dump()
        json_str = json.dumps(json_dict, ensure_ascii=False, indent=2)

        print("✅ 序列化成功")
        print(f"   - JSON 長度: {len(json_str)} 字元")
        print("   - 前 500 字元:")
        print(json_str[:500])

        # 驗證 JSON 可以被解析
        parsed = json.loads(json_str)
        print("\n✅ JSON 可以被解析")
        print(f"   - success: {parsed['success']}")
        print(f"   - data.query: {parsed['data']['query']}")
        print(f"   - data.articles 數量: {len(parsed['data']['articles'])}")

        # 顯示完整 JSON
        print("\n" + "=" * 60)
        print("完整 API 回應 JSON")
        print("=" * 60)
        print(json_str)

        return True

    except Exception as e:
        print(f"❌ 序列化失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_full_api_flow())

    print("\n" + "=" * 60)
    if success:
        print("✅ 所有測試通過！API 端點應該正常運作")
    else:
        print("❌ 測試失敗！需要修復")
    print("=" * 60)
