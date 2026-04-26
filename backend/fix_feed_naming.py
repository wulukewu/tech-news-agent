#!/usr/bin/env python3
"""
Fix RSS feed naming consistency - update underscore categories to proper theme names.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.supabase_service import SupabaseService

async def fix_feed_naming():
    """Fix RSS feed category naming to be consistent."""
    try:
        print("🔧 修復RSS源命名一致性...")
        
        supabase = SupabaseService()
        
        # 映射表：下底線格式 -> 主題格式
        category_mapping = {
            'educational_tutorial': 'Web Development & Programming',
            'educational_guide': 'Web Development & Programming', 
            'educational_reference': 'Web Development & Programming',
            'educational_news': 'Web Development & Programming',
            'official_reference': 'Official Documentation',
            'official_news': 'Official Updates',
            'community_tutorial': 'Community & Learning',
            'community_guide': 'Community & Learning'
        }
        
        # 獲取需要更新的feeds
        feeds_result = supabase.client.table('feeds').select('id, name, category').execute()
        
        updated_count = 0
        
        for feed in feeds_result.data:
            old_category = feed.get('category', '')
            
            if old_category in category_mapping:
                new_category = category_mapping[old_category]
                
                # 更新分類
                supabase.client.table('feeds').update({
                    'category': new_category
                }).eq('id', feed['id']).execute()
                
                print(f"  ✅ {feed['name']}: {old_category} -> {new_category}")
                updated_count += 1
        
        print(f"\n📊 更新完成: {updated_count} 個RSS源已修復")
        
        # 顯示最終分類統計
        final_feeds = supabase.client.table('feeds').select('category').execute()
        category_counts = {}
        
        for feed in final_feeds.data:
            category = feed.get('category', '未分類')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        print("\n📈 最終分類統計:")
        for category, count in sorted(category_counts.items()):
            print(f"  {category}: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        return False

async def main():
    """Main function."""
    print("🎯 RSS源命名一致性修復")
    print("=" * 40)
    
    success = await fix_feed_naming()
    
    if success:
        print("\n✅ 修復完成！RSS源命名現在更一致了。")
    else:
        print("\n❌ 修復失敗")

if __name__ == "__main__":
    asyncio.run(main())
