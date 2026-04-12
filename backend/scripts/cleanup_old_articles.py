#!/usr/bin/env python3
"""
清理舊的測試文章資料
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client

from app.core.config import settings


def cleanup_articles():
    """清理所有文章資料"""

    print("=" * 80)
    print("清理文章資料")
    print("=" * 80)
    print()

    # 初始化 Supabase client
    supabase = create_client(settings.supabase_url, settings.supabase_key)

    # 先查詢有多少文章
    try:
        count_result = supabase.table("articles").select("id", count="exact").execute()
        total_count = count_result.count if hasattr(count_result, "count") else 0

        print(f"📊 目前資料庫中有 {total_count} 篇文章")
        print()

        if total_count == 0:
            print("✅ 資料庫已經是空的，無需清理")
            return

        # 確認是否要刪除
        response = input(f"⚠️  確定要刪除所有 {total_count} 篇文章嗎？(yes/no): ")

        if response.lower() != "yes":
            print("❌ 取消清理操作")
            return

        print()
        print("🗑️  開始刪除文章...")

        # 刪除所有文章
        result = (
            supabase.table("articles")
            .delete()
            .neq("id", "00000000-0000-0000-0000-000000000000")
            .execute()
        )

        print("✅ 成功刪除所有文章")
        print()

        # 驗證刪除結果
        verify_result = supabase.table("articles").select("id", count="exact").execute()
        remaining_count = verify_result.count if hasattr(verify_result, "count") else 0

        print(f"📊 清理後剩餘文章數: {remaining_count}")

        if remaining_count == 0:
            print("✅ 清理完成！")
        else:
            print(f"⚠️  還有 {remaining_count} 篇文章未刪除")

    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    cleanup_articles()
