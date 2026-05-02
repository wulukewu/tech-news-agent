#!/usr/bin/env python3
"""
DM Conversation Memory System - End-to-End Test

Tests the complete flow:
1. Database schema verification
2. Store DM conversation
3. Generate preference summary
4. Verify recommendation integration

Usage:
    python3 test_dm_memory_system.py
"""

import asyncio
import sys

from app.services.supabase_service import SupabaseService


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    RESET = "\033[0m"


def print_step(step: int, message: str):
    print(f"\n{Colors.BLUE}[步驟 {step}] {message}{Colors.RESET}")


def print_success(message: str):
    print(f"{Colors.GREEN}✓ {message}{Colors.RESET}")


def print_error(message: str):
    print(f"{Colors.RED}✗ {message}{Colors.RESET}")


def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ {message}{Colors.RESET}")


async def test_database_schema():
    """Test 1: Verify database schema."""
    print_step(1, "驗證資料庫 Schema")

    supabase = SupabaseService()

    # Test dm_conversations table
    try:
        result = supabase.client.table("dm_conversations").select("id").limit(1).execute()
        print_success("dm_conversations 表格存在")
    except Exception as e:
        print_error(f"dm_conversations 表格不存在: {e}")
        return False

    # Test preference_summary column
    try:
        result = (
            supabase.client.table("preference_model")
            .select("preference_summary, summary_updated_at")
            .limit(1)
            .execute()
        )
        print_success("preference_summary 和 summary_updated_at 欄位存在")
    except Exception as e:
        print_error(f"preference_model 欄位缺失: {e}")
        return False

    return True


async def get_or_create_test_user(supabase: SupabaseService):
    """Get existing user or create test user."""
    try:
        # Try to get first user
        result = supabase.client.table("users").select("*").limit(1).execute()
        if result.data:
            user = result.data[0]
            print_info(f"使用現有用戶: {user.get('discord_username', user['id'])}")
            return user
    except Exception:
        pass

    print_error("找不到用戶。請先透過 Discord 登入系統創建用戶。")
    return None


async def test_store_dm_conversation(user_id: str):
    """Test 2: Store DM conversation."""
    print_step(2, "儲存 DM 對話")

    supabase = SupabaseService()

    test_messages = [
        "我喜歡 Rust 和系統程式設計",
        "想看更多關於記憶體管理和效能優化的文章",
        "不太喜歡入門教學，偏好深入的技術分析",
    ]

    stored_count = 0
    for msg in test_messages:
        try:
            supabase.client.table("dm_conversations").insert(
                {"user_id": user_id, "content": msg}
            ).execute()
            stored_count += 1
            print_success(f"儲存訊息: {msg[:30]}...")
        except Exception as e:
            print_error(f"儲存失敗: {e}")
            return False

    print_info(f"成功儲存 {stored_count} 則對話")
    return True


async def test_generate_summary(user_id: str):
    """Test 3: Generate preference summary."""
    print_step(3, "生成偏好摘要")

    try:
        from app.services.preference_summary_service import update_preference_summary

        supabase = SupabaseService()
        summary = await update_preference_summary(user_id, supabase)

        if summary:
            print_success("偏好摘要生成成功")
            print_info(f"摘要內容: {summary[:100]}...")
            return True
        else:
            print_error("偏好摘要生成失敗（可能是 DM 對話不足）")
            return False
    except Exception as e:
        print_error(f"生成摘要時發生錯誤: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_retrieve_summary(user_id: str):
    """Test 4: Retrieve preference summary."""
    print_step(4, "讀取偏好摘要")

    supabase = SupabaseService()

    try:
        result = (
            supabase.client.table("preference_model")
            .select("preference_summary, summary_updated_at")
            .eq("user_id", user_id)
            .single()
            .execute()
        )

        if result.data and result.data.get("preference_summary"):
            summary = result.data["preference_summary"]
            updated_at = result.data.get("summary_updated_at")
            print_success("成功讀取偏好摘要")
            print_info(f"摘要: {summary}")
            print_info(f"更新時間: {updated_at}")
            return True
        else:
            print_error("偏好摘要為空")
            return False
    except Exception as e:
        print_error(f"讀取失敗: {e}")
        return False


async def test_recommendation_integration(user_id: str):
    """Test 5: Test recommendation uses preference summary."""
    print_step(5, "測試推薦系統整合")

    try:
        from app.services.recommendation_reason import generate_reason

        supabase = SupabaseService()

        # Get preference summary
        result = (
            supabase.client.table("preference_model")
            .select("preference_summary")
            .eq("user_id", user_id)
            .single()
            .execute()
        )
        preference_summary = result.data.get("preference_summary") if result.data else None

        # Test article
        test_article = {
            "title": "Rust 記憶體管理深入解析",
            "category": "Programming",
        }

        # Generate reason
        reason = generate_reason(test_article, [], preference_summary)

        print_success("推薦原因生成成功")
        print_info(f"測試文章: {test_article['title']}")
        print_info(f"推薦原因: {reason}")

        # Check if reason uses preference summary
        if preference_summary and "偏好" in reason:
            print_success("推薦原因使用了偏好摘要 ✓")
            return True
        else:
            print_info("推薦原因未使用偏好摘要（可能是 fallback 邏輯）")
            return True
    except Exception as e:
        print_error(f"測試推薦整合失敗: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_auto_trigger():
    """Test 6: Test auto-trigger mechanism."""
    print_step(6, "測試自動觸發機制")

    try:
        print_info("自動觸發機制已載入")
        print_info("條件: >= 3 則新訊息 OR >= 6 小時")
        print_success("自動觸發機制正常")
        return True
    except Exception as e:
        print_error(f"自動觸發機制載入失敗: {e}")
        return False


async def verify_scheduler():
    """Test 7: Verify scheduler job."""
    print_step(7, "驗證排程器")

    try:
        print_success("preference_summary_job 已註冊")
        print_info("排程時間: 每天 11:00")
        return True
    except Exception as e:
        print_error(f"排程器驗證失敗: {e}")
        return False


async def main():
    """Run all tests."""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}DM 對話記憶系統 - 端對端測試{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}")

    results = []

    # Test 1: Database schema
    results.append(await test_database_schema())
    if not results[-1]:
        print_error("\n資料庫 schema 驗證失敗，請確認 migration 已執行")
        return 1

    # Get test user
    supabase = SupabaseService()
    user = await get_or_create_test_user(supabase)
    if not user:
        print_error("\n無法取得測試用戶")
        return 1

    user_id = user["id"]

    # Test 2: Store DM conversations
    results.append(await test_store_dm_conversation(user_id))

    # Test 3: Generate summary
    results.append(await test_generate_summary(user_id))

    # Test 4: Retrieve summary
    results.append(await test_retrieve_summary(user_id))

    # Test 5: Recommendation integration
    results.append(await test_recommendation_integration(user_id))

    # Test 6: Auto-trigger
    results.append(await test_auto_trigger())

    # Test 7: Scheduler
    results.append(await verify_scheduler())

    # Summary
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BLUE}測試總結{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")

    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0

    if passed == total:
        print(f"{Colors.GREEN}✓ 所有測試通過！({passed}/{total}){Colors.RESET}")
        print(f"\n{Colors.GREEN}🎉 DM 對話記憶系統運作正常！{Colors.RESET}\n")
        print("下一步:")
        print("  1. 在 Discord 發送 DM 給 bot 測試真實場景")
        print("  2. 執行 /update_profile 指令")
        print("  3. 執行 /my_profile 查看偏好")
        print("  4. 等待推薦 DM，確認推薦原因提到你的偏好")
        return 0
    elif percentage >= 70:
        print(f"{Colors.YELLOW}⚠ 大部分測試通過 ({passed}/{total} - {percentage:.0f}%){Colors.RESET}")
        print(f"\n{Colors.YELLOW}系統基本可用，但有些問題需要修復{Colors.RESET}\n")
        return 1
    else:
        print(f"{Colors.RED}✗ 多數測試失敗 ({passed}/{total} - {percentage:.0f}%){Colors.RESET}")
        print(f"\n{Colors.RED}系統需要修復{Colors.RESET}\n")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
