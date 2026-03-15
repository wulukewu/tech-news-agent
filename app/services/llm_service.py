import json
import logging
from typing import List, Optional
import asyncio

from openai import AsyncOpenAI
from app.core.config import settings
from app.schemas.article import ArticleSchema, AIAnalysis
from app.core.exceptions import LLMServiceError

logger = logging.getLogger(__name__)

# Constants for Models (Groq)
EVAL_MODEL = "llama-3.1-8b-instant"  
SUMMARIZE_MODEL = "llama-3.3-70b-versatile"

class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
        )
        
    async def evaluate_article(self, article: ArticleSchema) -> AIAnalysis:
        """Evaluate if an article is hardcore using a fast LLM."""
        logger.debug(f"Evaluating article: {article.title}")
        
        system_prompt = (
            "你是一個熱愛動手實作的硬核全端開發者，負責審查技術文章。\n"
            "你的任務是過濾掉無用的行銷廢話，只留下有價值的硬核技術資訊。\n"
            "請根據以下標準評估文章：\n"
            "1. 過濾行銷：是否包含具體程式碼、GitHub 連結或架構探討？純公告請淘汰。\n"
            "2. 行動價值：這項技術可以怎麼用在現有專案上？\n"
            "3. 折騰指數 (1-5分)：評估部署或上手的難易度 (例如有 Docker Compose 通常分數較低，需大量手動編譯則分數高)。\n\n"
            "⚠️ 絕對要求：你必須只回傳一個合法的 JSON，不要加上 Markdown 標記，例如 ```json。結構必須完全符合：\n"
            "{\n"
            '  "is_hardcore": boolean,\n'
            '  "reason": "一句話說明為什麼推薦或淘汰",\n'
            '  "actionable_takeaway": "提煉出的行動價值 (淘汰可留空)",\n'
            '  "tinkering_index": number\n'
            "}"
        )
        
        user_prompt = (
            f"文章標題：{article.title}\n"
            f"文章內容：{article.content_preview[:800]}"
        )
        
        try:
            response = await self.client.chat.completions.create(
                model=EVAL_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            
            content = response.choices[0].message.content
            if not content:
                raise LLMServiceError("Empty response from LLM")
                
            # Clean up potential markdown blocks if the model ignored instructions
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            
            return AIAnalysis(**data)
            
        except Exception as e:
            logger.warning(f"Failed to evaluate article '{article.title}', defaulting to not hardcore. Error: {e}")
            # Fallback defensively
            return AIAnalysis(
                is_hardcore=False,
                reason="解析失敗或評估超時",
                actionable_takeaway="",
                tinkering_index=0
            )

    async def evaluate_batch(self, set_of_articles: List[ArticleSchema]) -> List[ArticleSchema]:
        """Concurrently evaluate a list of articles."""
        logger.info(f"Evaluating {len(set_of_articles)} articles.")
        tasks = [self.evaluate_article(article) for article in set_of_articles]
        
        # We limit concurrency roughly to avoid hitting rate limits on OpenRouter
        semaphore = asyncio.Semaphore(5)
        
        async def sem_task(article, task):
            async with semaphore:
                result = await task
                article.ai_analysis = result
                return article
                
        # Gather all
        evaluated = await asyncio.gather(*(sem_task(a, t) for a, t in zip(set_of_articles, tasks)))
        
        # Filter for hardcore only
        hardcore_articles = [a for a in evaluated if getattr(a.ai_analysis, "is_hardcore", False)]
        logger.info(f"Retained {len(hardcore_articles)} hardcore articles out of {len(set_of_articles)}.")
        return hardcore_articles
        
    async def generate_weekly_newsletter(self, hardcore_articles: List[ArticleSchema]) -> Optional[str]:
        """Group top 7 hardcore articles into a beautiful Discord-ready Markdown."""
        if not hardcore_articles:
            return "本週沒有足夠硬核的技術資訊 🥲"
            
        # Limit to top 7 by sorting? (Or just taking the first 7 for now)
        # We can sort by tinkering index descending (most hardcore)
        hardcore_articles.sort(key=lambda x: x.ai_analysis.tinkering_index if x.ai_analysis else 0, reverse=True)
        top_articles = hardcore_articles[:7]
        
        draft = "請根據以下精選文章，幫我撰寫一份 Markdown 格式的「每週極客資訊報表」。\n\n"
        for a in top_articles:
            draft += f"---\n"
            draft += f"🏷️ 分類：{a.source_category}\n"
            draft += f"📌 標題：{a.title}\n"
            draft += f"🔗 連結：{a.url}\n"
            draft += f"💡 推薦原因：{a.ai_analysis.reason}\n"
            draft += f"🎯 行動價值：{a.ai_analysis.actionable_takeaway}\n"
            draft += f"🛠️ 折騰指數：{a.ai_analysis.tinkering_index} / 5\n\n"
            
        system_prompt = (
            "你是一位技術高超、熱愛開源與自架服務的全端工程師（同時也是我的專屬資訊策展人）。\n"
            "請根據以下草稿資料，排版出一份結構清晰、極具閱讀體驗的 Markdown 電子報。\n\n"
            "【任務要求】\n"
            "1. 開頭加上一段簡短、幽默且具有極客風格的本週前言（不要用 AI 罐頭語氣）。\n"
            "2. 將文章根據「🏷️ 分類」分開排版，使用 Markdown 的 Heading (##) 區隔。\n"
            "3. 每篇文章需包含 Markdown 格式的超連結（標題即連結）。\n"
            "4. 清楚呈現「💡 推薦原因」、「🎯 行動價值」與「🛠️ 折騰指數」（可以用 ⭐ 星號表示折騰程度）。\n"
            "5. 直接輸出 Markdown 內容，不要包含 ```markdown 標籤，也不要說「好的，這就為您產生...」。\n"
            "6. 總字數絕對不能超過 3,500 字元 (因為 Discord 的限制)。"
        )
        
        logger.info("Generating final weekly newsletter.")
        try:
            response = await self.client.chat.completions.create(
                model=SUMMARIZE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": draft}
                ],
                temperature=0.7,
                # Discord has a 4k character limit per message, 3500 is a safe target
                max_tokens=2000 
            )
            
            final_text = response.choices[0].message.content
            if final_text:
                return final_text.strip().replace("```markdown", "").replace("```", "").strip()
            return "無法生成報表內容。"
            
        except Exception as e:
            logger.error(f"Failed to generate weekly newsletter: {e}")
            raise LLMServiceError(f"Generation error: {e}")
