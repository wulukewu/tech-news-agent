#!/usr/bin/env python3
"""
Seed script for recommended RSS feeds in the onboarding system.

This script inserts curated recommended feeds with:
- is_recommended = True
- recommendation_priority (100 for top feeds, decreasing for others)
- description (user-friendly description)
- Categories: AI, Web Development, Security, DevOps, Cloud, etc.

Requirements: 2.2, 2.3, 12.5

Usage:
    python scripts/seed_recommended_feeds.py
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client


def main():
    """Main function to seed recommended feeds into Supabase database."""
    
    # Load environment variables from .env file
    load_dotenv()
    
    # Validate required environment variables
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url:
        raise ValueError(
            "Error: Missing required environment variable: SUPABASE_URL\n"
            "Please copy .env.example to .env and fill in the values"
        )
    
    if not supabase_key:
        raise ValueError(
            "Error: Missing required environment variable: SUPABASE_KEY\n"
            "Please copy .env.example to .env and fill in the values"
        )
    
    # Create Supabase client connection
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        print("Successfully connected to Supabase")
    except Exception as e:
        raise ConnectionError(
            f"Error: Failed to connect to Supabase\n"
            f"Please check:\n"
            f"1. SUPABASE_URL is correct (format: https://xxx.supabase.co)\n"
            f"2. SUPABASE_KEY is valid (check Supabase Dashboard > Settings > API)\n"
            f"3. Network connection is available\n"
            f"Details: {str(e)}"
        )
    recommended_feeds = [
        # AI Category (Priority 100-90)
        {
            "name": "OpenAI Blog",
            "url": "https://openai.com/blog/rss.xml",
            "category": "AI",
            "description": "最新的 AI 研究成果和產品更新，來自 ChatGPT 和 GPT-4 的開發團隊",
            "is_recommended": True,
            "recommendation_priority": 100,
            "is_active": True
        },
        {
            "name": "Simon Willison's Weblog",
            "url": "https://simonwillison.net/atom/everything/",
            "category": "AI",
            "description": "深入淺出的 AI 工具評測和實用技巧，涵蓋 LLM、提示工程和 AI 應用開發",
            "is_recommended": True,
            "recommendation_priority": 95,
            "is_active": True
        },
        {
            "name": "Anthropic Blog",
            "url": "https://www.anthropic.com/blog/rss.xml",
            "category": "AI",
            "description": "Claude AI 背後的研究團隊分享 AI 安全性和對齊研究",
            "is_recommended": True,
            "recommendation_priority": 90,
            "is_active": True
        },
        {
            "name": "Reddit r/LocalLLaMA",
            "url": "https://www.reddit.com/r/LocalLLaMA/.rss",
            "category": "AI",
            "description": "本地運行大型語言模型的社群討論，包含模型評測和優化技巧",
            "is_recommended": True,
            "recommendation_priority": 85,
            "is_active": True
        },
        
        # Web Development Category (Priority 89-75)
        {
            "name": "Hacker News",
            "url": "https://hnrss.org/frontpage",
            "category": "Web Development",
            "description": "科技圈最熱門的新聞和討論，涵蓋程式設計、創業和技術趨勢",
            "is_recommended": True,
            "recommendation_priority": 89,
            "is_active": True
        },
        {
            "name": "CSS-Tricks",
            "url": "https://css-tricks.com/feed/",
            "category": "Web Development",
            "description": "前端開發技巧、CSS 教學和網頁設計最佳實踐",
            "is_recommended": True,
            "recommendation_priority": 85,
            "is_active": True
        },
        {
            "name": "Smashing Magazine",
            "url": "https://www.smashingmagazine.com/feed/",
            "category": "Web Development",
            "description": "高品質的網頁設計和前端開發文章，涵蓋 UX、性能優化和可訪問性",
            "is_recommended": True,
            "recommendation_priority": 82,
            "is_active": True
        },
        {
            "name": "Vue.js News",
            "url": "https://news.vuejs.org/rss.xml",
            "category": "Web Development",
            "description": "Vue.js 官方新聞和社群精選文章",
            "is_recommended": True,
            "recommendation_priority": 78,
            "is_active": True
        },
        {
            "name": "React Blog",
            "url": "https://react.dev/rss.xml",
            "category": "Web Development",
            "description": "React 官方部落格，發布新功能和最佳實踐指南",
            "is_recommended": True,
            "recommendation_priority": 75,
            "is_active": True
        },
        
        # Security Category (Priority 88-70)
        {
            "name": "Krebs on Security",
            "url": "https://krebsonsecurity.com/feed/",
            "category": "Security",
            "description": "深度調查報導網路安全事件和資料外洩案例",
            "is_recommended": True,
            "recommendation_priority": 88,
            "is_active": True
        },
        {
            "name": "The Hacker News",
            "url": "https://feeds.feedburner.com/TheHackersNews",
            "category": "Security",
            "description": "最新的網路安全新聞、漏洞披露和威脅情報",
            "is_recommended": True,
            "recommendation_priority": 84,
            "is_active": True
        },
        {
            "name": "Schneier on Security",
            "url": "https://www.schneier.com/feed/atom/",
            "category": "Security",
            "description": "資安專家 Bruce Schneier 對安全、隱私和密碼學的深入分析",
            "is_recommended": True,
            "recommendation_priority": 80,
            "is_active": True
        },
        {
            "name": "OWASP Blog",
            "url": "https://owasp.org/blog/feed.xml",
            "category": "Security",
            "description": "Web 應用程式安全最佳實踐和漏洞防護指南",
            "is_recommended": True,
            "recommendation_priority": 70,
            "is_active": True
        },
        
        # DevOps Category (Priority 83-65)
        {
            "name": "Docker Blog",
            "url": "https://www.docker.com/blog/feed/",
            "category": "DevOps",
            "description": "容器化技術、Docker 最佳實踐和微服務架構",
            "is_recommended": True,
            "recommendation_priority": 83,
            "is_active": True
        },
        {
            "name": "Kubernetes Blog",
            "url": "https://kubernetes.io/feed.xml",
            "category": "DevOps",
            "description": "Kubernetes 官方部落格，涵蓋容器編排和雲原生應用",
            "is_recommended": True,
            "recommendation_priority": 80,
            "is_active": True
        },
        {
            "name": "HashiCorp Blog",
            "url": "https://www.hashicorp.com/blog/feed.xml",
            "category": "DevOps",
            "description": "基礎設施即代碼、Terraform、Vault 等 DevOps 工具",
            "is_recommended": True,
            "recommendation_priority": 72,
            "is_active": True
        },
        {
            "name": "Reddit r/devops",
            "url": "https://www.reddit.com/r/devops/.rss",
            "category": "DevOps",
            "description": "DevOps 社群討論、工具推薦和實戰經驗分享",
            "is_recommended": True,
            "recommendation_priority": 65,
            "is_active": True
        },
        
        # Cloud Category (Priority 81-68)
        {
            "name": "AWS News Blog",
            "url": "https://aws.amazon.com/blogs/aws/feed/",
            "category": "Cloud",
            "description": "AWS 新服務發布和雲端架構最佳實踐",
            "is_recommended": True,
            "recommendation_priority": 81,
            "is_active": True
        },
        {
            "name": "Google Cloud Blog",
            "url": "https://cloud.google.com/blog/rss",
            "category": "Cloud",
            "description": "Google Cloud Platform 產品更新和技術深度文章",
            "is_recommended": True,
            "recommendation_priority": 76,
            "is_active": True
        },
        {
            "name": "Azure Blog",
            "url": "https://azure.microsoft.com/en-us/blog/feed/",
            "category": "Cloud",
            "description": "Microsoft Azure 雲端服務和企業解決方案",
            "is_recommended": True,
            "recommendation_priority": 68,
            "is_active": True
        },
        
        # Programming Category (Priority 77-60)
        {
            "name": "GitHub Blog",
            "url": "https://github.blog/feed/",
            "category": "Programming",
            "description": "GitHub 新功能、開源專案和開發者工具",
            "is_recommended": True,
            "recommendation_priority": 77,
            "is_active": True
        },
        {
            "name": "Martin Fowler",
            "url": "https://martinfowler.com/feed.atom",
            "category": "Programming",
            "description": "軟體架構、重構和敏捷開發的經典文章",
            "is_recommended": True,
            "recommendation_priority": 73,
            "is_active": True
        },
        {
            "name": "Dev.to",
            "url": "https://dev.to/feed",
            "category": "Programming",
            "description": "開發者社群分享程式設計教學和專案經驗",
            "is_recommended": True,
            "recommendation_priority": 60,
            "is_active": True
        }
    ]
    
    print("Supabase client initialized successfully")
    print(f"Ready to seed {len(recommended_feeds)} recommended feeds...")
    print()
    
    # Check if the required columns exist
    print("Checking if feeds table has recommendation columns...")
    try:
        test_result = supabase.table('feeds').select('*').limit(1).execute()
        if test_result.data and len(test_result.data) > 0:
            columns = test_result.data[0].keys()
            required_columns = ['is_recommended', 'recommendation_priority', 'description']
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                print(f"\n❌ Error: Missing required columns in feeds table: {', '.join(missing_columns)}")
                print("\nThe feeds table needs to be extended with recommendation columns first.")
                print("Please apply migration 003 before running this script:")
                print("\n  1. Using Supabase Dashboard SQL Editor:")
                print("     Copy and paste: scripts/migrations/003_extend_feeds_table_for_recommendations.sql")
                print("\n  2. Or using psql (if DATABASE_URL is set):")
                print("     psql $DATABASE_URL -f scripts/migrations/003_extend_feeds_table_for_recommendations.sql")
                print("\n  3. Or using the migration script:")
                print("     cd scripts/migrations && ./apply_migration.sh 003_extend_feeds_table_for_recommendations.sql")
                return 1
            else:
                print("✓ All required columns exist")
    except Exception as e:
        print(f"Warning: Could not verify schema: {e}")
        print("Proceeding anyway...")
    
    print()
    
    # Insert feeds with error handling
    inserted_count = 0
    skipped_count = 0
    updated_count = 0
    
    for feed in recommended_feeds:
        try:
            # Check if feed with this URL already exists
            existing = supabase.table('feeds').select('id, name, url').eq('url', feed['url']).execute()
            
            if existing.data and len(existing.data) > 0:
                # Update existing feed to mark as recommended
                feed_id = existing.data[0]['id']
                update_data = {
                    'is_recommended': feed['is_recommended'],
                    'recommendation_priority': feed['recommendation_priority'],
                    'description': feed['description']
                }
                supabase.table('feeds').update(update_data).eq('id', feed_id).execute()
                updated_count += 1
                print(f"↻ Updated (marked as recommended): {feed['name']}")
            else:
                # Insert new feed
                supabase.table('feeds').insert(feed).execute()
                inserted_count += 1
                print(f"✓ Inserted: {feed['name']} (Priority: {feed['recommendation_priority']})")
                
        except Exception as e:
            error_message = str(e).lower()
            
            # Handle missing column error
            if 'could not find' in error_message and 'column' in error_message:
                print(f"\n❌ Error: The feeds table is missing required columns")
                print("Please apply migration 003_extend_feeds_table_for_recommendations.sql first")
                print("See instructions above.")
                return 1
            
            # Handle duplicate URL error (shouldn't happen with our check, but just in case)
            elif 'duplicate' in error_message or 'unique' in error_message:
                skipped_count += 1
                print(f"⊘ Skipped (duplicate URL): {feed['name']}")
                continue
            
            # Handle connection errors
            elif 'connection' in error_message or 'network' in error_message or 'timeout' in error_message:
                raise ConnectionError(
                    f"Error: Network error while processing feed '{feed['name']}'\n"
                    f"Please check your internet connection and try again\n"
                    f"If the problem persists, check Supabase status at status.supabase.com\n"
                    f"Details: {str(e)}"
                )
            
            # Re-raise other unexpected errors
            else:
                raise Exception(
                    f"Error: Unexpected error while processing feed '{feed['name']}'\n"
                    f"Details: {str(e)}"
                )
    
    # Print summary
    print()
    print("="*60)
    print("Seeding completed!")
    print(f"Successfully inserted: {inserted_count} feeds")
    if updated_count > 0:
        print(f"Updated (marked as recommended): {updated_count} feeds")
    if skipped_count > 0:
        print(f"Skipped (duplicates): {skipped_count} feeds")
    print(f"Total recommended feeds: {inserted_count + updated_count}")
    print("="*60)
    print()
    print("Categories covered:")
    categories = {}
    for feed in recommended_feeds:
        cat = feed['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {category}: {count} feeds")
    
    return 0


if __name__ == "__main__":
    exit(main())
