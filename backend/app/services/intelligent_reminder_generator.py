"""
Intelligent Reminder Generator - 智能提醒生成服務
分析用戶閱讀習慣，使用 LLM 生成個性化提醒
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class IntelligentReminderGenerator:
    """生成智能提醒的核心服務"""

    def __init__(self):
        self.supabase = SupabaseService()
        self.llm = LLMService()

    async def generate_reminders_for_user(self, user_id: str) -> List[Dict]:
        """為用戶生成智能提醒"""
        try:
            # 1. 檢查用戶設定
            settings = await self._get_user_settings(user_id)
            if not settings.get("enabled", True):
                logger.info(f"Reminders disabled for user {user_id}")
                return []

            # 2. 分析用戶閱讀習慣
            user_profile = await self._analyze_user_reading_habits(user_id)
            if not user_profile:
                logger.info(f"No reading history for user {user_id}")
                return []

            # 3. 找出候選文章
            candidate_articles = await self._find_candidate_articles(user_id, user_profile)
            if not candidate_articles:
                logger.info(f"No candidate articles for user {user_id}")
                return []

            # 4. 使用 LLM 生成提醒內容
            reminders = await self._generate_reminder_content(
                user_id, user_profile, candidate_articles, settings
            )

            # 5. 保存到資料庫
            saved_reminders = await self._save_reminders(user_id, reminders)

            logger.info(f"Generated {len(saved_reminders)} reminders for user {user_id}")
            return saved_reminders

        except Exception as e:
            logger.error(f"Error generating reminders for user {user_id}: {e}")
            return []

    async def _get_user_settings(self, user_id: str) -> Dict:
        """獲取用戶提醒設定"""
        try:
            result = (
                self.supabase.client.table("reminder_settings")
                .select("*")
                .eq("user_id", user_id)
                .execute()
            )
            if result.data:
                return result.data[0]
            return {"enabled": True, "max_daily_reminders": 5}
        except Exception as e:
            logger.error(f"Error getting user settings: {e}")
            return {"enabled": True, "max_daily_reminders": 5}

    async def _analyze_user_reading_habits(self, user_id: str) -> Optional[Dict]:
        """分析用戶閱讀習慣"""
        try:
            # 獲取用戶的閱讀列表和評分
            result = (
                self.supabase.client.table("reading_list")
                .select("*, articles(*)")
                .eq("user_id", user_id)
                .execute()
            )

            if not result.data:
                return None

            # 分析偏好
            high_rated = [
                item for item in result.data if item.get("rating") and item["rating"] >= 4
            ]
            categories = {}
            total_articles = len(result.data)

            for item in result.data:
                article = item.get("articles", {})
                category = article.get("category", "general")
                categories[category] = categories.get(category, 0) + 1

            return {
                "total_read": total_articles,
                "high_rated_count": len(high_rated),
                "favorite_categories": sorted(categories.items(), key=lambda x: x[1], reverse=True)[
                    :3
                ],
                "avg_tinkering_index": sum(
                    item.get("articles", {}).get("tinkering_index", 0) for item in result.data
                )
                / max(total_articles, 1),
            }

        except Exception as e:
            logger.error(f"Error analyzing reading habits: {e}")
            return None

    async def _find_candidate_articles(self, user_id: str, user_profile: Dict) -> List[Dict]:
        """找出適合推薦的文章"""
        try:
            # 獲取用戶已讀過的文章 ID
            read_result = (
                self.supabase.client.table("reading_list")
                .select("article_id")
                .eq("user_id", user_id)
                .execute()
            )
            read_article_ids = [item["article_id"] for item in read_result.data]

            # 找出未讀的文章
            query = self.supabase.client.table("articles").select("*")

            if read_article_ids:
                query = query.not_.in_("id", read_article_ids)

            result = query.order("published_at", desc=True).limit(10).execute()

            return result.data

        except Exception as e:
            logger.error(f"Error finding candidate articles: {e}")
            return []

    async def _generate_reminder_content(
        self, user_id: str, user_profile: Dict, articles: List[Dict], settings: Dict
    ) -> List[Dict]:
        """使用 LLM 生成提醒內容"""
        try:
            max_reminders = settings.get("max_daily_reminders", 5)
            reminders = []

            for article in articles[:max_reminders]:
                # 構建 prompt
                prompt = self._build_reminder_prompt(user_profile, article)

                # 調用 LLM
                response = await self.llm.client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that creates personalized article reminders.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.7,
                    max_tokens=200,
                )

                content = response.choices[0].message.content.strip()

                # 計算優先級分數
                priority_score = self._calculate_priority_score(article, user_profile)

                reminders.append(
                    {
                        "article_id": article["id"],
                        "title": article["title"],
                        "description": content,
                        "priority_score": priority_score,
                        "action_url": article.get("url"),
                        "reading_time_estimate": self._estimate_reading_time(article),
                    }
                )

            return reminders

        except Exception as e:
            logger.error(f"Error generating reminder content: {e}")
            return []

    def _build_reminder_prompt(self, user_profile: Dict, article: Dict) -> str:
        """構建 LLM prompt"""
        favorite_cats = user_profile.get("favorite_categories", [])
        cat_str = (
            ", ".join([str(cat[0]) for cat in favorite_cats if cat and cat[0]]) or "general tech"
        )

        return f"""Create a brief, engaging reminder message for this article.

User's reading preferences:
- Favorite categories: {cat_str}
- Average technical depth preference: {user_profile.get('avg_tinkering_index', 0.5):.1f}/1.0

Article:
- Title: {article.get('title', 'Untitled')}
- Category: {article.get('category') or 'general'}
- Technical depth: {article.get('tinkering_index', 0.5):.1f}/1.0

Write a 1-2 sentence reminder that highlights why this article matches their interests.
Keep it concise and actionable."""

    def _calculate_priority_score(self, article: Dict, user_profile: Dict) -> float:
        """計算提醒優先級分數 (0-1)"""
        score = 0.5

        # 技術深度匹配度
        ti_diff = abs(
            article.get("tinkering_index", 0.5) - user_profile.get("avg_tinkering_index", 0.5)
        )
        score += (1 - ti_diff) * 0.3

        # 分類匹配度
        article_category = article.get("category", "")
        favorite_cats = [cat for cat, _ in user_profile.get("favorite_categories", [])]
        if article_category in favorite_cats:
            score += 0.2

        return min(max(score, 0.0), 1.0)

    def _estimate_reading_time(self, article: Dict) -> int:
        """估算閱讀時間（分鐘）"""
        # 簡單估算：假設平均閱讀速度 200 字/分鐘
        title_length = len(article.get("title", ""))
        summary_length = len(article.get("ai_summary", ""))
        total_chars = title_length + summary_length

        # 估算：每 400 字符約 1 分鐘
        return max(int(total_chars / 400), 1)

    async def _save_reminders(self, user_id: str, reminders: List[Dict]) -> List[Dict]:
        """保存提醒到資料庫"""
        saved = []
        for reminder in reminders:
            try:
                result = (
                    self.supabase.client.table("reminder_log")
                    .insert(
                        {
                            "user_id": user_id,
                            "reminder_type": "personalized_article",
                            "reminder_context": {
                                "title": reminder["title"],
                                "description": reminder["description"],
                                "priority_score": reminder["priority_score"],
                                "reading_time_estimate": reminder["reading_time_estimate"],
                                "action_url": reminder["action_url"],
                            },
                            "sent_at": datetime.now(timezone.utc).isoformat(),
                            "channel": "discord",
                            "status": "pending",
                        }
                    )
                    .execute()
                )
                if result.data:
                    saved.append(result.data[0])
            except Exception as e:
                logger.error(f"Error saving reminder: {e}")

        return saved
