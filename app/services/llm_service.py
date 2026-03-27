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

        # Semaphore limits true concurrency to avoid hitting Groq rate limits.
        # The coroutine is created *inside* sem_task so it only starts executing
        # once the semaphore slot is acquired (not at list-comprehension time).
        semaphore = asyncio.Semaphore(5)

        async def sem_task(article: ArticleSchema) -> ArticleSchema:
            async with semaphore:
                article.ai_analysis = await self.evaluate_article(article)
                return article

        evaluated = await asyncio.gather(*(sem_task(a) for a in set_of_articles))
        
        # Filter for hardcore only
        hardcore_articles = [a for a in evaluated if getattr(a.ai_analysis, "is_hardcore", False)]
        logger.info(f"Retained {len(hardcore_articles)} hardcore articles out of {len(set_of_articles)}.")
        return hardcore_articles
        
    async def generate_deep_dive(self, article: ArticleSchema) -> str:
        """Generate a deep-dive technical analysis for a single article in Traditional Chinese."""
        logger.debug(f"Generating deep dive for article: {article.title}")

        system_prompt = (
            "你是一位資深技術分析師，請以繁體中文針對以下文章提供深度技術分析。\n"
            "分析必須包含以下四個部分：\n"
            "1. 🔍 核心技術概念：說明文章涉及的核心技術原理與概念。\n"
            "2. 🚀 應用場景：描述此技術可應用的實際場景與使用案例。\n"
            "3. ⚠️ 潛在風險：列出採用此技術可能面臨的風險或限制。\n"
            "4. 👣 建議下一步：提供具體可行的下一步行動建議。\n\n"
            "請直接輸出分析內容，不要加上多餘的前言或結語。"
        )

        # Build user prompt; use only title if content_preview is empty
        if article.content_preview:
            content_section = f"文章內容預覽：{article.content_preview}\n"
        else:
            content_section = ""

        ai_section = ""
        if article.ai_analysis:
            ai_section = (
                f"AI 初步評估：\n"
                f"  推薦原因：{article.ai_analysis.reason}\n"
                f"  行動價值：{article.ai_analysis.actionable_takeaway}\n"
                f"  折騰指數：{article.ai_analysis.tinkering_index} / 5\n"
            )

        user_prompt = (
            f"文章標題：{article.title}\n"
            f"文章分類：{article.source_category}\n"
            f"{content_section}"
            f"{ai_section}"
        )

        try:
            response = await self.client.chat.completions.create(
                model=SUMMARIZE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=600
            )

            content = response.choices[0].message.content
            if not content or not content.strip():
                return "無法生成深度摘要內容。"
            return content.strip()

        except Exception as e:
            logger.error(f"Failed to generate deep dive for '{article.title}': {e}")
            raise LLMServiceError(f"Deep dive generation error: {e}")

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

    async def generate_digest_intro(self, hardcore_articles: List[ArticleSchema]) -> str:
        """Generate a Traditional Chinese technical trend intro (≤300 chars) with humorous geek style.
        
        On failure, returns default fallback text without raising exceptions.
        """
        logger.debug(f"Generating digest intro for {len(hardcore_articles)} hardcore articles.")

        titles_text = "\n".join(f"- {a.title}" for a in hardcore_articles[:10])

        system_prompt = (
            "你是一位幽默風趣的極客技術編輯，請以繁體中文撰寫本週技術趨勢前言。\n"
            "要求：\n"
            "1. 風格幽默且具極客氣息，避免罐頭語氣。\n"
            "2. 總字數不超過 300 字。\n"
            "3. 直接輸出前言內容，不要加上多餘的前言或結語。"
        )

        user_prompt = f"本週精選技術文章如下：\n{titles_text}"

        try:
            response = await self.client.chat.completions.create(
                model=SUMMARIZE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=400
            )

            content = response.choices[0].message.content
            if not content or not content.strip():
                raise LLMServiceError("Empty response from LLM")
            return content.strip()

        except Exception as e:
            logger.error(f"Failed to generate digest intro, using fallback: {e}")
            return "本週精選技術文章，請展開各項目查看詳情。"

    async def generate_reading_recommendation(
        self,
        titles: List[str],
        categories: List[str]
    ) -> str:
        """根據高評分文章的標題與分類，生成不超過 500 字的繁體中文推薦摘要。"""
        logger.debug(f"Generating reading recommendation for {len(titles)} articles.")

        titles_text = "\n".join(f"- {t}" for t in titles)
        categories_text = "、".join(sorted(set(categories)))

        user_prompt = (
            f"以下是使用者近期評分 4 星以上的高評分文章：\n\n"
            f"文章標題：\n{titles_text}\n\n"
            f"涵蓋分類：{categories_text}"
        )

        system_prompt = (
            "你是一位技術閱讀顧問，請根據使用者的高評分文章，以繁體中文撰寫一份閱讀推薦摘要。\n"
            "摘要需包含：\n"
            "1. 使用者目前關注的技術主題與趨勢分析。\n"
            "2. 建議持續追蹤的技術關鍵字與主題方向。\n"
            "3. 下一步閱讀建議。\n\n"
            "⚠️ 要求：\n"
            "- 全程使用繁體中文。\n"
            "- 摘要總字數不超過 500 字。\n"
            "- 直接輸出摘要內容，不要加上多餘的前言或結語。"
        )

        try:
            response = await self.client.chat.completions.create(
                model=SUMMARIZE_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            content = response.choices[0].message.content
            if not content or not content.strip():
                raise LLMServiceError("Empty response from LLM")
            return content.strip()

        except LLMServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to generate reading recommendation: {e}")
            raise LLMServiceError(f"Reading recommendation generation error: {e}")
