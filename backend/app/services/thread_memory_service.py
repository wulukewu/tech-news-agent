from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import UUID

import httpx

from app.core.logger import get_logger
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.services.llm_service import LLMService
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)

DEFAULT_TOKEN_LIMIT = 3000
DEFAULT_RECENT_MESSAGE_COUNT = 8
DEFAULT_SYSTEM_PROMPT = (
    "你是 Tech News Agent 的技術助理。請根據提供的摘要記憶、相關文章脈絡與最近對話，" "給出準確、可行、可追溯到脈絡的回答。若資訊不足，請明確說明。"
)
_INTERNAL_BASE_URL = "http://localhost:8000"


class ThreadMemoryService:
    def __init__(
        self,
        supabase_service: Optional[SupabaseService] = None,
        llm_service: Optional[LLMService] = None,
        token_limit: int = DEFAULT_TOKEN_LIMIT,
        recent_message_count: int = DEFAULT_RECENT_MESSAGE_COUNT,
    ) -> None:
        self.supabase_service = supabase_service or SupabaseService()
        self.llm_service = llm_service or LLMService()
        self.token_limit = token_limit
        self.recent_message_count = recent_message_count
        self._conversation_repo = ConversationRepository(self.supabase_service.client)
        self._message_repo = MessageRepository(self.supabase_service.client)

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        cjk_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        latin_words = len(re.findall(r"\b\w+\b", text))
        return max(1, cjk_chars + int(latin_words * 0.75))

    async def get_or_create_thread_conversation(
        self,
        user_id: str,
        thread_id: str,
        title: str,
        article_id: Optional[str] = None,
    ):
        existing = await self._conversation_repo.get_conversation_by_thread_id(
            user_id=user_id, thread_id=thread_id
        )
        if existing:
            return existing

        metadata: dict[str, str] = {"source": "discord_thread"}
        if article_id:
            metadata["article_id"] = article_id

        return await self._conversation_repo.create_conversation(
            user_id=user_id,
            title=title[:120],
            platform="discord",
            metadata=metadata,
            thread_id=thread_id,
        )

    async def save_user_message(
        self, conversation_id: str | UUID, thread_id: str, query: str
    ) -> None:
        await self._message_repo.add_message(
            conversation_id=conversation_id,
            role="user",
            content=query,
            platform="discord",
            thread_id=thread_id,
            approx_tokens=self.estimate_tokens(query),
        )

    async def save_assistant_message(
        self, conversation_id: str | UUID, thread_id: str, content: str
    ) -> None:
        await self._message_repo.add_message(
            conversation_id=conversation_id,
            role="assistant",
            content=content,
            platform="discord",
            thread_id=thread_id,
            approx_tokens=self.estimate_tokens(content),
        )

    async def get_recent_messages(self, thread_id: str) -> list[dict[str, str]]:
        messages = await self._message_repo.get_messages_by_thread(
            thread_id=thread_id, limit=self.recent_message_count * 2, ascending=False
        )
        messages.reverse()
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def get_unsummarized_messages(self, thread_id: str) -> list:
        return await self._message_repo.get_messages_by_thread(
            thread_id=thread_id, limit=200, ascending=True, unsummarized_only=True
        )

    @staticmethod
    def _format_rag_context(articles: list) -> str:
        if not articles:
            return ""
        parts: list[str] = []
        for idx, article in enumerate(articles[:5], start=1):
            parts.append(f"[{idx}] 標題: {article.title}\n摘要: {article.summary}\n連結: {article.url}")
        return "\n\n".join(parts)

    async def build_prompt_payload(
        self, conversation_id: str | UUID, thread_id: str, articles: list
    ) -> dict:
        row = (
            self.supabase_service.client.table("conversations")
            .select("summary_buffer")
            .eq("id", str(conversation_id))
            .limit(1)
            .execute()
        )
        summary = row.data[0].get("summary_buffer") if row.data else ""
        recent_messages = await self.get_recent_messages(thread_id)
        return {
            "summary": summary or "",
            "rag_context": self._format_rag_context(articles),
            "recent_messages": recent_messages,
        }

    async def should_compress(self, conversation_id: str | UUID, thread_id: str) -> bool:
        conversation_row = (
            self.supabase_service.client.table("conversations")
            .select("summary_buffer")
            .eq("id", str(conversation_id))
            .limit(1)
            .execute()
        )
        summary_tokens = 0
        if conversation_row.data:
            summary_tokens = self.estimate_tokens(
                conversation_row.data[0].get("summary_buffer") or ""
            )

        unsummarized = await self.get_unsummarized_messages(thread_id)
        unsummarized_tokens = sum((msg.approx_tokens or 0) for msg in unsummarized)
        return summary_tokens + unsummarized_tokens >= self.token_limit

    async def compress_history(self, conversation_id: str | UUID, thread_id: str) -> None:
        unsummarized = await self.get_unsummarized_messages(thread_id)
        if len(unsummarized) <= self.recent_message_count * 2:
            return

        to_summarize = unsummarized[: -self.recent_message_count * 2]
        latest_kept = unsummarized[-self.recent_message_count * 2 :]

        old_summary_resp = (
            self.supabase_service.client.table("conversations")
            .select("summary_buffer")
            .eq("id", str(conversation_id))
            .limit(1)
            .execute()
        )
        old_summary = (
            old_summary_resp.data[0].get("summary_buffer", "") if old_summary_resp.data else ""
        )

        history_lines = []
        if old_summary:
            history_lines.append(f"既有摘要:\n{old_summary}")
        history_lines.append("新增歷史對話:")
        for msg in to_summarize:
            history_lines.append(f"{msg.role}: {msg.content}")
        history_text = "\n".join(history_lines)

        summary = await self.llm_service.summarize_conversation_buffer(history_text)

        now_iso = datetime.now(timezone.utc).isoformat()
        self.supabase_service.client.table("conversations").update(
            {
                "summary_buffer": summary,
                "summary_updated_at": now_iso,
                "summarized_until_message_at": to_summarize[-1].created_at.isoformat(),
                "approx_token_count": self.estimate_tokens(summary)
                + sum((m.approx_tokens or 0) for m in latest_kept),
            }
        ).eq("id", str(conversation_id)).execute()

        for msg in to_summarize:
            self.supabase_service.client.table("conversation_messages").update(
                {"is_summarized": True}
            ).eq("id", str(msg.id)).execute()

    async def maybe_schedule_compression(
        self,
        conversation_id: str | UUID,
        thread_id: str,
        schedule_func: Optional[Callable[..., Any]] = None,
    ) -> None:
        if not await self.should_compress(conversation_id, thread_id):
            return

        if schedule_func:
            schedule_func(self.compress_history, conversation_id, thread_id)
            return

        # Delegate to FastAPI BackgroundTasks via internal endpoint so the
        # compression lifecycle is managed by the web process, not the bot loop.
        try:
            async with httpx.AsyncClient(base_url=_INTERNAL_BASE_URL, timeout=5.0) as client:
                await client.post(
                    "/internal/compress-thread",
                    json={"conversation_id": str(conversation_id), "thread_id": thread_id},
                )
        except Exception as exc:
            # Fall back to asyncio task if the HTTP call fails (e.g. bot-only mode).
            logger.warning(
                "Internal compress-thread call failed, falling back to asyncio.create_task: %s",
                exc,
            )
            asyncio.create_task(self.compress_history(conversation_id, thread_id))

    async def process_thread_query(
        self,
        user_id: str,
        thread_id: str,
        query: str,
        title: str,
        article_id: Optional[str] = None,
        schedule_func: Optional[Callable[[Callable, tuple], None]] = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
    ) -> dict:
        from app.api._qa_helpers import _search_articles_by_query

        conversation = await self.get_or_create_thread_conversation(
            user_id=user_id, thread_id=thread_id, title=title, article_id=article_id
        )
        await self.save_user_message(conversation.id, thread_id, query)
        articles = await _search_articles_by_query(query)
        payload = await self.build_prompt_payload(conversation.id, thread_id, articles)
        answer = await self.llm_service.generate_thread_answer(
            system_prompt=system_prompt,
            summary=payload["summary"],
            rag_context=payload["rag_context"],
            recent_messages=payload["recent_messages"],
            user_query=query,
        )
        await self.save_assistant_message(conversation.id, thread_id, answer)
        await self.maybe_schedule_compression(
            conversation_id=conversation.id,
            thread_id=thread_id,
            schedule_func=schedule_func,
        )
        return {
            "conversation_id": str(conversation.id),
            "answer": answer,
            "articles": articles,
        }
