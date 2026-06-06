import asyncio
import json
import logging
from typing import Dict, List

from openai import APIConnectionError, APIStatusError, APITimeoutError, AsyncOpenAI, RateLimitError
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.core.exceptions import LLMServiceError
from app.schemas.article import AIAnalysis, ArticleSchema

logger = logging.getLogger(__name__)

# Constants for Models (Groq)
EVAL_MODEL = "llama-3.1-8b-instant"
SUMMARIZE_MODEL = "llama-3.3-70b-versatile"

# Retry configuration (kept for reference; tenacity decorators use these values)
MAX_RETRIES = 3
API_TIMEOUT = 30  # seconds

# Exceptions that are safe to retry (transient)
_RETRYABLE_EXCEPTIONS = (RateLimitError, APIConnectionError, APITimeoutError)


def _is_retryable_status(exc: BaseException) -> bool:
    """Return True for 429 / 5xx APIStatusError responses."""
    if isinstance(exc, APIStatusError):
        return exc.status_code in (429, 500, 502, 503, 504)
    return False


class LLMService:
    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://api.groq.com/openai/v1",
            api_key=settings.groq_api_key,
            timeout=API_TIMEOUT,
        )

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    async def _call_groq(self, api_call_func, context: str):
        """Call Groq API with tenacity exponential-backoff retry.

        Retries on:
        - RateLimitError (HTTP 429)
        - APIConnectionError (network issues)
        - APITimeoutError (timeout)
        - APIStatusError with 5xx status codes

        Non-retryable errors (e.g. 400 Bad Request) are raised immediately.
        """
        try:
            return await api_call_func()
        except APIStatusError as exc:
            if _is_retryable_status(exc):
                logger.warning(f"Retryable HTTP {exc.status_code} from Groq for {context}: {exc}")
                raise APIConnectionError(
                    message=str(exc), request=exc.request
                ) from exc  # re-raise as retryable
            logger.error(f"Non-retryable Groq API error ({exc.status_code}) for {context}: {exc}")
            raise

    async def evaluate_article(self, article: ArticleSchema) -> AIAnalysis | None:
        """Evaluate if an article is hardcore using a fast LLM."""
        logger.debug(f"Evaluating article: {article.title}")

        system_prompt = (
            "你是一個熱愛動手實作且極具理論深度的硬核全端開發者，負責審核與評估技術文章。\n"
            "請對文章進行精準且客觀的三維度技術評估：\n\n"
            "【維度 1：實作與折騰複雜度 (Practical Complexity - 1-5分)】\n"
            "評估動手配置、寫代碼、編譯或部署的折騰難易度：\n"
            "- 1分：純觀點散文/新聞、無任何代碼/命令或僅有極少代碼片段。\n"
            "- 2分：簡單，有清晰指南、單個 CLI 命令或基礎 Docker Compose 執行。\n"
            "- 3分：中等，有完整代碼/配置文件，上手需要進行部分配置與本地偵錯。\n"
            "- 4分：困難，需要手動編譯、複雜的多模組配置、或深度環境偵錯。\n"
            "- 5分：極端困難，需要深入理解底層、無文檔編譯核心或大量耗時偵錯。\n\n"
            "【維度 2：理論與概念深度 (Theoretical Depth - 1-5分)】\n"
            "評估電腦科學理論、演算法、分佈式原理或底層系統設計的深度：\n"
            "- 1分：淺顯的新聞、基礎產品發布、無任何架構或理論探討。\n"
            "- 2分：日常開發小技巧、單個 API 的使用方法。\n"
            "- 3分：包含中階系統架構設計、性能分析、優化策略或設計模式探討。\n"
            "- 4分：涉及分佈式一致性協定、底層操作系統原理、密碼學或極複雜的資安漏洞分析。\n"
            "- 5分：前沿學術論文、全新底層理論架構、或極高深的計算理論剖析。\n\n"
            "【維度 3：專案行動價值 (Actionability - 1-5分)】\n"
            "評估此內容對現代全端/後端 web 開發者在專案落地上是否有直接的實用性或參考價值：\n"
            "- 1分：與軟體開發無直接關聯（如科普趣聞、硬體發布）。\n"
            "- 2分：一般性行業觀點、趨勢分析或無法落地的概念性產品。\n"
            "- 3分：與現代開發主流技術相關的實用工具介紹或最佳實踐指南。\n"
            "- 4分：能指導現有專案進行代碼重構、顯著提升效能、或解決常見的工程痛點。\n"
            "- 5分：能直接解決重大安全隱患、顛覆性降低系統成本、或解決極關鍵工程阻礙的實戰指南。\n\n"
            "【評分對齊錨點範例 (Few-Shot Anchors)】\n"
            '- 範例 A (水文/新聞)："AI 晶片大廠發布全新效能卡，市場反應熱烈"\n'
            "  * 評分分析：實作=1, 理論=1, 行動=1 (content_type=news)\n"
            '- 範例 B (一般教學/工具介紹)："如何使用 Express.js 與 Docker 快速部署一個 Hello World App"\n'
            "  * 評分分析：實作=2, 理論=2, 行動=3 (content_type=tutorial)\n"
            '- 範例 C (中階實用指南)："使用 Redis 實作分散式限流器的最佳實踐與 Lua 腳本優化"\n'
            "  * 評分分析：實作=3, 理論=3, 行動=4 (content_type=guide)\n"
            '- 範例 D (硬核高難度文章)："手把手帶你用 Rust 從零寫一個相容 Redis 協議的異步併發 Key-Value 資料庫"\n'
            "  * 評分分析：實作=5, 理論=4, 行動=4 (content_type=project)\n\n"
            "⚠️ 絕對要求：你必須只回傳一個合法的 JSON，不要加上 Markdown 標記（如 ```json）。結構必須完全符合：\n"
            "{\n"
            '  "is_hardcore": boolean,\n'
            '  "reason": "請使用流暢的繁體中文撰寫，說明推薦或淘汰原因 (限制 50 字以內)",\n'
            '  "actionable_takeaway": "請使用流暢的繁體中文撰寫，提煉出對開發者的行動價值 (淘汰可留空，限制 50 字以內)",\n'
            '  "content_type": "tutorial|guide|reference|project|news|opinion",\n'
            '  "practical_complexity": number (必須是 1 到 5 之間的整數),\n'
            '  "theoretical_depth": number (必須是 1 到 5 之間的整數),\n'
            '  "actionability": number (必須是 1 到 5 之間的整數)\n'
            "}"
        )

        user_prompt = f"文章標題：{article.title}\n文章分類：{article.category}"
        if article.content_preview:
            user_prompt += f"\n\n文章內容摘錄：\n{article.content_preview}"

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

            response = await self._call_groq(
                make_api_call, context=f"evaluate_article('{article.title}')"
            )

            content = response.choices[0].message.content
            if not content:
                raise LLMServiceError("Empty response from LLM")

            # Clean up potential markdown blocks if the model ignored instructions
            content = content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)

            # 提取 LLM 回傳的原始指標分數，在 Python 端進行權重公式計算
            practical = int(data.get("practical_complexity", 1))
            theoretical = int(data.get("theoretical_depth", 1))
            actionability = int(data.get("actionability", 1))
            content_type = data.get("content_type", "news")

            # 邊界值防禦：限制在 1-5 範圍內
            practical = max(1, min(5, practical))
            theoretical = max(1, min(5, theoretical))
            actionability = max(1, min(5, actionability))

            # 針對 news 和 opinion 的實作複雜度強制設上限
            if content_type in ("news", "opinion"):
                practical = max(1, min(2, practical))

            # 依據 content_type 進行加權公式計算
            if content_type in ("tutorial", "project"):
                raw_score = 0.5 * practical + 0.3 * theoretical + 0.2 * actionability
            elif content_type in ("guide", "reference"):
                raw_score = 0.3 * practical + 0.4 * theoretical + 0.3 * actionability
            else:  # news / opinion / 預設
                raw_score = 0.1 * practical + 0.6 * theoretical + 0.3 * actionability

            # 嚴格的 Python 四捨五入
            tinkering_index = int(raw_score + 0.5)
            tinkering_index = max(1, min(5, tinkering_index))

            # 寫入 AIAnalysis，保持與舊 Schema 欄位相容
            return AIAnalysis(
                is_hardcore=bool(data.get("is_hardcore", False)),
                reason=str(data.get("reason", "")),
                actionable_takeaway=str(data.get("actionable_takeaway", "")),
                tinkering_index=tinkering_index,
                content_type=content_type,
            )

        except (RateLimitError, APIConnectionError, APITimeoutError) as e:
            logger.error(
                f"Rate limit or connection error during evaluation of '{article.title}': {e}"
            )
            raise
        except Exception as e:
            logger.warning(
                f"Failed to evaluate article '{article.title}', returning None. Error: {e}"
            )
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
            "你是一位資深技術分析師，請以繁體中文為以下技術文章寫一段自然、易讀的摘要。\n\n"
            "摘要風格：\n"
            "- 用自然的語言描述，避免制式化的條列格式\n"
            "- 重點說明技術的核心價值和實際應用\n"
            "- 如果有值得關注的技術細節或趨勢，簡潔提及\n"
            "- 語調專業但不生硬，像是跟同事分享技術見解\n\n"
            "請直接輸出摘要內容，不超過 200 字。"
        )

        user_prompt = f"文章標題：{article.title}\n文章分類：{article.category}"

        # Add content if available (best source), else fall back to ai_analysis
        if article.content_preview:
            user_prompt += f"\n\n文章內容摘錄：\n{article.content_preview}"
        elif article.ai_analysis:
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

            response = await self._call_groq(
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
        # Free tier: 6000 TPM, ~500 tokens/article → max 12 articles/min
        # Use 1 concurrent request with 6s delay = 10 req/min, ~5000 TPM (safe margin)
        semaphore = asyncio.Semaphore(1)

        tinkering_failed_count = 0
        tinkering_success_count = 0
        summary_failed_count = 0
        summary_success_count = 0

        async def process_article(article: ArticleSchema) -> ArticleSchema:
            nonlocal tinkering_failed_count, tinkering_success_count
            nonlocal summary_failed_count, summary_success_count

            async with semaphore:
                # Add delay to respect rate limits (skip in test environment)
                import os

                if os.getenv("APP_ENV") != "test":
                    await asyncio.sleep(10)

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
                                # Also extract content_type if present
                                if article.ai_analysis.content_type:
                                    article.content_type = article.ai_analysis.content_type
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

            response = await self._call_groq(
                make_api_call, context=f"generate_deep_dive('{article.title}')"
            )

            content = response.choices[0].message.content
            if not content or not content.strip():
                return "無法生成深度摘要內容。"
            return content.strip()

        except Exception as e:
            logger.error(f"Failed to generate deep dive for '{article.title}': {e}")
            raise LLMServiceError(f"Deep dive generation error: {e}")

    async def generate_takeaway(self, article_id: str) -> str:
        """取得或生成文章的 1 句話技術核心精華（混合快取模式）

        優先讀取資料庫已有的 actionable_takeaway；若無，則動態調用 LLM 生成，
        將其寫回/快取至資料庫，並返回。
        """
        from app.services.supabase_service import SupabaseService

        supabase = SupabaseService()

        logger.info(f"Retrieving or generating takeaway for article {article_id}")

        try:
            # 1. 優先查詢資料庫是否已有快取
            response = (
                supabase.client.table("articles")
                .select("title, category, actionable_takeaway, ai_summary")
                .eq("id", str(article_id))
                .execute()
            )
            if response and response.data:
                row = response.data[0]
                cached_takeaway = row.get("actionable_takeaway")
                if cached_takeaway and cached_takeaway.strip():
                    logger.info(f"Takeaway cache hit for article {article_id}")
                    return cached_takeaway.strip()

                title = row.get("title", "未知文章")
                category = row.get("category", "技術")
                ai_summary = row.get("ai_summary", "")
            else:
                title = "未知文章"
                category = "技術"
                ai_summary = ""
        except Exception as e:
            logger.warning(f"Failed to query database for article {article_id} takeaway: {e}")
            title = "未知文章"
            category = "技術"
            ai_summary = ""

        # 2. 快取未命中，實時調用 LLM 生成「極簡 1 句話核心精華」
        logger.info(f"Takeaway cache miss for article {article_id}, generating via LLM...")

        system_prompt = (
            "你是一位資深技術分析師，請以繁體中文為以下技術文章寫一句最核心、最硬核的「1 句話技術核心精華」（不超過 50 字）。\n"
            "風格要求：\n"
            "- 用極度精鍊、一針見血的語言描述技術的核心本質與最具行動價值的要點。\n"
            "- 絕不拖泥帶水，直接給出最關鍵的 Takeaway，不含任何前言或結語。\n"
            "- 不要以『這篇文章...』或『作者指出...』開頭，直接說明技術本質。不超過 50 字。"
        )

        user_prompt = f"文章標題：{title}\n文章分類：{category}\nAI 摘要：{ai_summary}"

        try:
            # Use Groq client to generate
            async def make_api_call():
                return await self.client.chat.completions.create(
                    model=SUMMARIZE_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.7,
                    max_tokens=150,
                )

            response = await self._call_groq(make_api_call, context=f"generate_takeaway('{title}')")

            takeaway = response.choices[0].message.content
            if not takeaway or not takeaway.strip():
                takeaway = "無法生成核心精華內容。"
            else:
                takeaway = takeaway.strip()

                # 3. 快取寫回資料庫
                try:
                    (
                        supabase.client.table("articles")
                        .update({"actionable_takeaway": takeaway})
                        .eq("id", str(article_id))
                        .execute()
                    )
                    logger.info(
                        f"Successfully cached generated takeaway to database for article {article_id}"
                    )
                except Exception as cache_exc:
                    logger.warning(
                        f"Failed to cache generated takeaway to database for article {article_id}: {cache_exc}"
                    )

            return takeaway

        except Exception as e:
            logger.error(f"Failed to generate takeaway for '{title}': {e}")
            return "生成技術精華失敗，請稍後再試。"

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

            response = await self._call_groq(make_api_call, context="generate_weekly_newsletter")

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
            f"以下是使用者近期評分 4 星以上的高評分文章：\n\n" f"文章標題：\n{titles_text}\n\n" f"涵蓋分類：{categories_text}"
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

            response = await self._call_groq(
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

    async def summarize_conversation_buffer(self, history_text: str) -> str:
        """Compress long thread history into a compact summary."""
        if not history_text.strip():
            return ""

        system_prompt = (
            "你是對話記憶壓縮器。請將對話整理成可供後續問答使用的精簡摘要，"
            "保留：使用者目標、已確認事實、未解決問題、限制與偏好。"
            "請用繁體中文，避免冗語，控制在 300 字以內。"
        )

        try:

            async def make_api_call():
                return await self.client.chat.completions.create(
                    model=EVAL_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": history_text},
                    ],
                    temperature=0.2,
                    max_tokens=400,
                )

            response = await self._call_groq(make_api_call, context="summarize_conversation_buffer")
            content = response.choices[0].message.content
            if not content:
                raise LLMServiceError("Empty summary response")
            return content.strip()
        except Exception as e:
            logger.error(f"Failed to summarize conversation buffer: {e}")
            raise LLMServiceError(f"Summary buffer generation error: {e}")

    async def generate_thread_answer(
        self,
        system_prompt: str,
        summary: str,
        rag_context: str,
        recent_messages: List[Dict[str, str]],
        user_query: str,
    ) -> str:
        """Generate answer with System Prompt + Summary + RAG + Recent dialog."""
        try:
            messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]

            if summary:
                messages.append({"role": "system", "content": f"摘要記憶：\n{summary}"})
            if rag_context:
                messages.append({"role": "system", "content": f"RAG 內容：\n{rag_context}"})

            for msg in recent_messages[-12:]:
                role = msg.get("role")
                content = (msg.get("content") or "").strip()
                if role in {"user", "assistant"} and content:
                    messages.append({"role": role, "content": content})

            messages.append({"role": "user", "content": user_query})

            async def make_api_call():
                return await self.client.chat.completions.create(
                    model=SUMMARIZE_MODEL,
                    messages=messages,
                    temperature=0.4,
                    max_tokens=800,
                )

            response = await self._call_groq(make_api_call, context="generate_thread_answer")
            content = response.choices[0].message.content
            if not content or not content.strip():
                raise LLMServiceError("Empty thread answer response")
            return content.strip()

        except Exception as e:
            logger.error(f"Failed to generate thread answer: {e}")
            raise LLMServiceError(f"Thread answer generation error: {e}")
