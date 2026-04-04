"""
Example demonstrating SupabaseService context manager usage

This example shows how to use the SupabaseService with async context manager
for automatic resource cleanup.
"""
import asyncio
from app.services.supabase_service import SupabaseService


async def example_with_context_manager():
    """
    使用 async context manager 的範例
    
    當使用 async with 語法時，資源會在離開 context 時自動清理。
    這是推薦的使用方式，因為它確保資源總是被正確清理，
    即使在發生例外的情況下也是如此。
    """
    print("Example 1: Using async context manager")
    
    async with SupabaseService() as service:
        print("Inside context - service is active")
        # 在這裡使用 service 進行資料庫操作
        # 例如：
        # users = await service.get_active_feeds()
        # await service.save_to_reading_list(discord_id, article_id)
        
    print("Outside context - resources automatically cleaned up")
    print()


async def example_with_exception_handling():
    """
    展示 context manager 在例外情況下的行為
    
    即使在 context 內部發生例外，close() 方法仍然會被呼叫，
    確保資源被正確清理。
    """
    print("Example 2: Context manager with exception handling")
    
    try:
        async with SupabaseService() as service:
            print("Inside context - about to raise an exception")
            # 模擬發生錯誤
            raise ValueError("Something went wrong!")
    except ValueError as e:
        print(f"Caught exception: {e}")
        print("Resources were still cleaned up despite the exception")
    
    print()


async def example_manual_cleanup():
    """
    手動清理資源的範例
    
    如果不使用 context manager，你需要手動呼叫 close() 方法。
    這種方式較不推薦，因為容易忘記清理資源。
    """
    print("Example 3: Manual resource cleanup (not recommended)")
    
    service = SupabaseService()
    try:
        print("Service created - performing operations")
        # 在這裡使用 service
        # ...
    finally:
        # 確保在 finally 區塊中清理資源
        await service.close()
        print("Resources manually cleaned up")
    
    print()


async def example_nested_context_managers():
    """
    展示巢狀 context manager 的使用
    
    你可以在同一個 async with 語句中使用多個 context manager。
    """
    print("Example 4: Nested context managers")
    
    # 注意：通常你不需要多個 SupabaseService 實例，
    # 這只是展示語法的範例
    async with SupabaseService() as service1:
        print("First service active")
        async with SupabaseService() as service2:
            print("Second service also active")
            # 使用兩個 service
        print("Second service cleaned up")
    print("First service cleaned up")
    print()


async def main():
    """執行所有範例"""
    print("=" * 60)
    print("SupabaseService Context Manager Usage Examples")
    print("=" * 60)
    print()
    
    await example_with_context_manager()
    await example_with_exception_handling()
    await example_manual_cleanup()
    await example_nested_context_managers()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    # 執行範例
    asyncio.run(main())
