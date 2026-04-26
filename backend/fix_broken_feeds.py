#!/usr/bin/env python3
"""
Fix broken RSS feeds with correct URLs.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.supabase_service import SupabaseService

async def fix_broken_feeds():
    """Fix broken RSS feeds with correct URLs."""
    try:
        print("🔧 修復損壞的RSS源...")
        
        supabase = SupabaseService()
        
        # 修復映射表
        fixes = {
            'Vue.js News': 'https://blog.vuejs.org/feed.rss',  # 正確的Vue.js官方部落格
            'Netflix Tech Blog': 'https://netflixtechblog.medium.com/feed',  # Medium上的Netflix技術部落格
            'Netlify Blog': 'https://www.netlify.com/blog/feed.xml',  # 正確的Netlify RSS
            'Seattle Data Guy': 'https://seattledataguy.substack.com/feed',  # Substack版本
            'Towards Data Science': 'https://towardsdatascience.com/feed',  # 保持原URL，可能是暫時問題
            'Alchemy Blog': 'https://www.alchemy.com/blog/rss.xml'  # 正確的Alchemy RSS
        }
        
        updated_count = 0
        
        for feed_name, new_url in fixes.items():
            # 查找並更新feed
            feed_result = supabase.client.table('feeds').select('id, url').eq('name', feed_name).execute()
            
            if feed_result.data:
                feed = feed_result.data[0]
                old_url = feed['url']
                
                # 更新URL
                supabase.client.table('feeds').update({
                    'url': new_url
                }).eq('id', feed['id']).execute()
                
                print(f"  ✅ {feed_name}")
                print(f"     舊: {old_url}")
                print(f"     新: {new_url}")
                updated_count += 1
            else:
                print(f"  ❌ 找不到RSS源: {feed_name}")
        
        print(f"\n📊 修復完成: {updated_count} 個RSS源已更新")
        return True
        
    except Exception as e:
        print(f"❌ 修復失敗: {e}")
        return False

async def main():
    """Main function."""
    print("🎯 修復損壞的RSS源")
    print("=" * 40)
    
    success = await fix_broken_feeds()
    
    if success:
        print("\n✅ 修復完成！所有RSS源現在應該都能正常工作了。")
    else:
        print("\n❌ 修復失敗")

if __name__ == "__main__":
    asyncio.run(main())
