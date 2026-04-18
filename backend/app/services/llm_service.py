import asyncio
import json
import logging

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.schemas.article import AIAnalysis, ArticleSchema

logger = logging.getLogger(__name__)

# Constants for Models (Groq)
EVAL_MODEL = "llama-3.1-8b-instant"
SUMMARIZE_MODEL = "llama-3.3-70b-versatile"

# Retry configuration
MAX_RETRIES = 2
RETRY_DELAYS = [2, 4]  # seconds
API_TIMEOUT = 30  # seconds


class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            timeout=API_TIMEOUT,
        )

    async def _call_api_with_retry(self, api_call_func, context: str):
        """
        Call API with exponential backoff retry logic.

        Args:
            api_call_func: Async function that makes the API call
            context: Description of the API call for logging

        Returns:
            API response

        Raises:
            Exception: If all retries fail
        """
        last_exception = None

        for attempt in range(MAX_RETRIES + 1):  # 0, 1, 2 (total 3 attempts: initial + 2 retries)
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt}/{MAX_RETRIES} for {context}")

                response = await api_call_func()
                return response

            except Exception as e:
                last_exception = e

                # Check if this is the last attempt
                if attempt >= MAX_RETRIES:
                    logger.error(
                        f"All retry attempts exhausted for {context}. " f"Final error: {e!s}"
                    )
                    raise

                # Check for Retry-After header (for rate limiting)
                retry_after = None
                if hasattr(e, "response") and hasattr(e.response, "headers"):
                    retry_after = e.response.headers.get("Retry-After")

                if retry_after:
                    try:
                        delay = float(retry_after)
                        logger.warning(
                            f"Rate limited for {context}. "
                            f"Retry-After header indicates {delay}s delay. "
                            f"Attempt {attempt + 1}/{MAX_RETRIES + 1}"
                        )
                    except (ValueError, TypeError):
                        # If Retry-After is not a valid number, use exponential backoff
                        delay = RETRY_DELAYS[attempt]
                        logger.warning(
                            f"API error for {context}: {e!s}. "
                            f"Retrying in {delay}s. Attempt {attempt + 1}/{MAX_RETRIES + 1}"
                        )
                else:
                    # Use exponential backoff delay
                    delay = RETRY_DELAYS[attempt]
                    logger.warning(
                        f"API error for {context}: {e!s}. "
                        f"Retrying in {delay}s. Attempt {attempt + 1}/{MAX_RETRIES + 1}"
                    )

                await asyncio.sleep(delay)

        # This should never be reached, but just in case
        raise last_exception if last_exception else Exception("Unknown error in retry logic")

    async def evaluate_article(self, article: ArticleSchema) -> AIAnalysis:
        """Evaluate if an article is hardcore using a fast LLM."""
        logger.debug(f"Evaluating article: {article.title}")

        system_prompt = (
            "你是一個熱愛動手實作的硬核全端開發者,負責審查技術文章。\n"
            "你的任務是過濾掉無用的行銷廢話，只留下有價值的硬核技術資訊。\n"
            "請根據以下標準評估文章：\n"
            "1. 過濾行銷：是否包含具體程式碼、GitHub 連結或架構探討？純公告請淘汰。\n"
            "2. 行動價值：這項技術可以怎麼用在現有專案上？\n"
            "3. 折騰指數 (1-5分)：評估部署或上手的難易度\n"
            "   - 1分：非常簡單，有完整文檔和一鍵部署\n"
            "   - 2分：簡單，有 Docker Compose 或清晰指南\n"
            "   - 3分：中等，需要一些配置和調試\n"
            "   - 4分：困難，需要手動編譯或複雜配置\n"
            "   - 5分：非常困難，需要深入理解和大量調試\n\n"
            "⚠️ 重要：tinkering_index 必須是 1 到 5 之間的整數，不能是 0 或其他值。\n\n"
            "⚠️ 絕對要求：你必須只回傳一個合法的 JSON，不要加上 Markdown 標記，例如 ```json。結構必須完全符合：\n"
            "{\n"
            '  "is_hardcore": boolean,\n'
            '  "reason": "一句話說明為什麼推薦或淘汰",\n'
            '  "actionable_takeaway": "提煉出的行動價值 (淘汰可留空)",\n'
            '  "tinkering_index": number (必須是 1-5 之間的整數)\n'
            "}"
        )

        user_prompt = f"文章標題：{article.title}\n" f"文章分類：{article.category}"

        try:
            # Use retry wrapper for API call
            async def make_api_call():
                return await self.client.chat.completions.create(
                    model=EVAL_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1,
                )

            response = await self._call_api_with_retry(
                make_api_call, context=f"evaluate_article('{article.title}')"
            )

            content = response.choices[0].message.content
            if not content:
                raise LLMServiceError("Empty response from LLM")

            # Clean up potential markdown blocks if the model ignored instructions
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)

            return AIAnalysis(**data)

        except Exception as e:
            logger.warning(
                f"Failed to evaluate article '{article.title}', defaulting to not hardcore. Error: {e}"
            )
            # Fallback defensively - return None to indicate failure
            # This will be handled by the caller (evaluate_batch)
            return None

    async def generate_summary(self, article: ArticleSchema) -> str | None:
        """
        Generate ai_summary for a single article using a powerful LLM.

        Args:
            article: Article to generate summary for

        Returns:
            Generated summary string, or None on failure
        """
        logger.debug(f"Generating summary for article: {article.title}")

        system_prompt = (
            "你是一位資深技術分析師，請以繁體中文針對以下文章提供簡潔的技術摘要。\n"
            "摘要必須包含：\n"
            "1. 核心技術概念：說明文章涉及的核心技術原理。\n"
            "2. 應用場景：描述此技術可應用的實際場景。\n"
            "3. 建議下一步：提供具體可行的下一步行動建議。\n\n"
            "請直接輸出摘要內容，不要加上多餘的前言或結語。摘要應簡潔明瞭，不超過 300 字。"
        )

        user_prompt = f"文章標題：{article.title}\n" f"文章分類：{article.category}"

        # Add ai_analysis info if available
        if article.ai_analysis:
            user_prompt += (
                f"\n\nAI 初步評估：\n"
                f"  推薦原因：{article.ai_analysis.reason}\n"
                f"  行動價值：{article.ai_analysis.actionable_takeaway}\n"
                f"  折騰指數：{article.ai_analysis.tinkering_index} / 5"
            )

        try:
            # Use retry wrapper for API call
            async def make_api_call():
                return await self.client.chat.completions.create(
                    model=SUMMARIZE_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=500,
                )

            response = await self._call_api_with_retry(
                make_api_call, context=f"generate_summary('{article.title}')"
            )

            content = response.choices[0].message.content
            if not content or not content.strip():
                logger.warning(f"Empty summary generated for article '{article.title}'")
                return None

            return content.strip()

        except Exception as e:
            logger.error(
                f"Failed to generate summary for article '{article.title}' (URL: {article.url}). "
                f"Error: {e!s}"
            )
            return None

    async def evaluate_batch(self, set_of_articles: list[ArticleSchema]) -> list[ArticleSchema]:
        """
        Concurrently evaluate a list of articles with improved error handling.

        For each article:
        - Call evaluate_tinkering_index() if tinkering_index is NULL
        - Call generate_summary() if ai_summary is NULL
        - On failure, set respective fields to NULL and continue

        Returns:
            Articles with populated ai_analysis fields (or NULL on failure)
        """
        logger.info(f"Evaluating {len(set_of_articles)} articles.")

        # Semaphore limits true concurrency to avoid hitting Groq rate limits.
        # Free tier: 30 RPM, so we use 2 concurrent requests with delays
        semaphore = asyncio.Semaphore(2)

        tinkering_failed_count = 0
        tinkering_success_count = 0
        summary_failed_count = 0
        summary_success_count = 0

        async def process_article(article: ArticleSchema) -> ArticleSchema:
            nonlocal tinkering_failed_count, tinkering_success_count
            nonlocal summary_failed_count, summary_success_count

            async with semaphore:
                # Add delay to respect rate limits
                # Free tier: 30 RPM = 2 seconds per request minimum
                # With 2 concurrent, we need 4 seconds delay to stay under 30 RPM
                # (60 seconds / 30 requests) × 2 concurrent = 4 seconds
                await asyncio.sleep(4)

                # Process tinkering_index if it's NULL
                if article.tinkering_index is None:
                    try:
                        # Attempt to evaluate the article
                        article.ai_analysis = await self.evaluate_article(article)

                        # Extract tinkering_index from ai_analysis
                        if article.ai_analysis and hasattr(article.ai_analysis, "tinkering_index"):
                            # Validate tinkering_index range
                            ti = article.ai_analysis.tinkering_index
                            if isinstance(ti, int) and 1 <= ti <= 5:
                                article.tinkering_index = ti
                                tinkering_success_count += 1
                            else:
                                logger.warning(
                                    f"Invalid tinkering_index {ti} from LLM for article '{article.title}'. "
                                    f"Setting to None."
                                )
                                article.tinkering_index = None
                                article.ai_analysis = None
                                tinkering_failed_count += 1
                        else:
                            # ai_analysis is None (evaluation failed)
                            article.tinkering_index = None
                            article.ai_analysis = None
                            tinkering_failed_count += 1

                    except Exception as e:
                        # On API failure, set tinkering_index to NULL and log error
                        logger.error(
                            f"Failed to evaluate tinkering_index for article '{article.title}' (URL: {article.url}). "
                            f"Error: {e!s}"
                        )

                        article.tinkering_index = None
                        article.ai_analysis = None
                        tinkering_failed_count += 1

                # Process ai_summary if it's NULL
                if article.ai_summary is None:
                    try:
                        # Attempt to generate summary
                        summary = await self.generate_summary(article)
                        article.ai_summary = summary

                        if summary is not None:
                            summary_success_count += 1
                        else:
                            summary_failed_count += 1

                    except Exception as e:
                        # On API failure, set ai_summary to NULL and log error
                        logger.error(
                            f"Failed to generate summary for article '{article.title}' (URL: {article.url}). "
                            f"Error: {e!s}"
                        )

                        article.ai_summary = None
                        summary_failed_count += 1

                return article

        # Process all articles (successful and failed)
        evaluated = await asyncio.gather(*(process_article(a) for a in set_of_articles))

        # Log warning if more than 30% of articles failed
        total_articles = len(set_of_articles)
        if total_articles > 0:
            tinkering_total = tinkering_success_count + tinkering_failed_count
            summary_total = summary_success_count + summary_failed_count

            if tinkering_total > 0:
                tinkering_failure_rate = tinkering_failed_count / tinkering_total
                if tinkering_failure_rate > 0.3:
                    logger.warning(
                        f"High tinkering_index failure rate: {tinkering_failed_count}/{tinkering_total} "
                        f"({tinkering_failure_rate:.1%}) failed. This may indicate API issues."
                    )

            if summary_total > 0:
                summary_failure_rate = summary_failed_count / summary_total
                if summary_failure_rate > 0.3:
                    logger.warning(
                        f"High ai_summary failure rate: {summary_failed_count}/{summary_total} "
                        f"({summary_failure_rate:.1%}) failed. This may indicate API issues."
                    )

        logger.info(
            f"Batch evaluation complete: "
            f"tinkering_index ({tinkering_success_count} successful, {tinkering_failed_count} failed), "
            f"ai_summary ({summary_success_count} successful, {summary_failed_count} failed) "
            f"out of {total_articles} articles."
        )

        # Return all articles (both successful and failed)
        return evaluated

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

        # Build user prompt with available fields
        user_prompt = f"文章標題：{article.title}\n" f"文章分類：{article.category}\n"

        ai_section = ""
        if article.ai_analysis:
            ai_section = (
                f"AI 初步評估：\n"
                f"  推薦原因：{article.ai_analysis.reason}\n"
                f"  行動價值：{article.ai_analysis.actionable_takeaway}\n"
                f"  折騰指數：{article.ai_analysis.tinkering_index} / 5\n"
            )
            user_prompt += ai_section

        try:
            # Use retry wrapper for API call
            async def make_api_call():
                return await self.client.chat.completions.create(
                    model=SUMMARIZE_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=600,
                )

            response = await self._call_api_with_retry(
                make_api_call, context=f"generate_deep_dive('{article.title}')"
            )

            content = response.choices[0].message.content
            if not content or not content.strip():
                return "無法生成深度摘要內容。"
            return content.strip()

        except Exception as e:
            logger.error(f"Failed to generate deep dive for '{article.title}': {e}")
            raise LLMServiceError(f"Deep dive generation error: {e}")

    async def generate_weekly_newsletter(
        self, hardcore_articles: list[ArticleSchema]
    ) -> str | None:
        """Group top 7 hardcore articles into a beautiful Discord-ready Markdown."""
        if not hardcore_articles:
            return "本週沒有足夠硬核的技術資訊 🥲"

        # Limit to top 7 by sorting? (Or just taking the first 7 for now)
        # We can sort by tinkering index descending (most hardcore)
        hardcore_articles.sort(
            key=lambda x: x.ai_analysis.tinkering_index if x.ai_analysis else 0, reverse=True
        )
        top_articles = hardcore_articles[:7]

        draft = "請根據以下精選文章，幫我撰寫一份 Markdown 格式的「每週極客資訊報表」。\n\n"
        for a in top_articles:
            draft += "---\n"
            draft += f"🏷️ 分類：{a.category}\n"
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
            # Use retry wrapper for API call
            async def make_api_call():
                return await self.client.chat.completions.create(
                    model=SUMMARIZE_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": draft},
                    ],
                    temperature=0.7,
                    # Discord has a 4k character limit per message, 3500 is a safe target
                    max_tokens=2000,
                )

            response = await self._call_api_with_retry(
                make_api_call, context="generate_weekly_newsletter"
            )

            final_text = response.choices[0].message.content
            if final_text:
                return final_text.strip().replace("```markdown", "").replace("```", "").strip()
            return "無法生成報表內容。"

        except Exception as e:
            logger.error(f"Failed to generate weekly newsletter: {e}")
            raise LLMServiceError(f"Generation error: {e}")

    async def generate_reading_recommendation(
        self, titles: list[str], categories: list[str]
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
            # Use retry wrapper for API call
            async def make_api_call():
                return await self.client.chat.completions.create(
                    model=SUMMARIZE_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=800,
                )

            response = await self._call_api_with_retry(
                make_api_call, context="generate_reading_recommendation"
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
