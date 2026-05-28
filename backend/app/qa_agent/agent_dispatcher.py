import json
import re
from typing import Any, Dict, List, Optional

from app.core.logger import get_logger
from app.services.llm_service import EVAL_MODEL, LLMService
from app.services.supabase_service import SupabaseService

logger = get_logger(__name__)


class QAAgentDispatcher:
    def __init__(
        self,
        supabase_service: Optional[SupabaseService] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.supabase_service = supabase_service or SupabaseService()
        self.llm_service = llm_service or LLMService()

    async def dispatch(
        self,
        user_id: str,
        discord_id: str,
        query: str,
        history_turns: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Dispatch user query based on intent, system state, subscriptions, and preferences.
        Returns a dictionary containing:
        - action: 'chat' | 'record_preference' | 'search'
        - search_query: str | None
        - memory_to_record: str | None
        - reply_content: str | None
        """
        # 1. Fetch user preference profile
        pref_summary = "尚無偏好摘要。在對話中告訴我你喜歡或不喜歡的主題（例如『我偏好系統設計』），我會幫你記住！"
        cat_weights = {}
        try:
            resp = (
                self.supabase_service.client.table("preference_model")
                .select("preference_summary, category_weights")
                .eq("user_id", user_id)
                .single()
                .execute()
            )
            if resp.data:
                pref_summary = resp.data.get("preference_summary") or pref_summary
                cat_weights = resp.data.get("category_weights") or {}
        except Exception as e:
            logger.warning(f"Failed to fetch preference profile for user {user_id}: {e}")

        # 2. Fetch user subscriptions
        subs_text = "目前無任何訂閱。建議引導使用者使用 `/add_feed` 指令訂閱一些技術 RSS 來源。"
        try:
            subscriptions = await self.supabase_service.get_user_subscriptions(discord_id)
            if subscriptions:
                subs_lines = []
                for sub in subscriptions:
                    subs_lines.append(f"- {sub.name} (分類: {sub.category})")
                subs_text = "\n".join(subs_lines)
        except Exception as e:
            logger.warning(f"Failed to fetch subscriptions for user {discord_id}: {e}")

        # 3. Format history turns
        history_text = "無前述對話歷史。"
        if history_turns:
            hist_lines = []
            for turn in history_turns[-5:]:  # limit to last 5 turns for efficiency
                role = "User" if turn.get("is_user") else "Assistant"
                text = turn.get("content", "")
                hist_lines.append(f"{role}: {text}")
            history_text = "\n".join(hist_lines)

        # 4. Construct System Prompt
        system_prompt = (
            "你是一個高智能、貼心的個人技術新聞 AI 助理（Agent Dispatcher）。\n"
            "你的工作是分析使用者的輸入，並決定最合適的行為（Action）。你對系統的功能瞭若指掌，且說話專業、溫暖、精簡，使用繁體中文（Taiwan）。\n\n"
            "【系統能力與斜線指令介紹】\n"
            "使用者可以使用以下 Discord 斜線指令與系統進行深入交互，當用戶想做這些事時，你應該口頭親切地指引他們使用對應的指令：\n"
            "- `/news_now`：查看最新推薦技術新聞（支援分頁與分類篩選）\n"
            "- `/reading_list`：查看與管理你存下來的待讀清單\n"
            "- `/my_profile`：查看自己的偏好檔案、摘要與最關注的前 5 大技術分類權重\n"
            "- `/update_profile`：強制根據 DM 對話立即重新生成並更新偏好摘要\n"
            "- `/recommend_now`：立即產生個人化技術新聞推薦，並發送到你的 Discord DM\n\n"
            "【使用者當前上下文】\n"
            f"1. 訂閱的 RSS 來源列表：\n{subs_text}\n\n"
            f"2. 個人偏好摘要：\n{pref_summary}\n\n"
            f"3. 分類權重設定：\n{json.dumps(cat_weights, ensure_ascii=False)}\n\n"
            f"【多輪對話歷史】\n{history_text}\n\n"
            "【你必須採取的行動（Action）類型】\n"
            "分析使用者目前的輸入，並從中選擇一個行動（Action）：\n"
            "1. `chat`：使用者在進行閒聊、打招呼（如「你好」）、詢問一般技術概念（如「解釋一下什麼是 HMR？」）、**詢問系統功能/詢問你能做什麼（例如「你能找文章給我嗎？」、「你能幫我推薦文章嗎？」、「你要怎麼推薦？」）**。\n"
            "   - **重要限制**：如果使用者只是在問你「能不能...」、「會不會...」或者只是泛泛地說「我想看文章」（未指定具體技術關鍵字或主題），你應該選擇 `chat` 來介紹你的功能並親切引導他，**千萬不要**選擇 `search`，否則會導致系統用空泛的關鍵字去資料庫盲目搜尋。\n"
            "   - 你需要在 `reply_content` 中用繁體中文熱情、專業且貼心地回答，並適時指引他們可以使用對應的 Discord 斜線指令（如 `/news_now`, `/recommend_now`）。\n"
            '2. `record_preference`：使用者明確表達了他喜歡/不喜歡的主題（例如「我想多看一些系統設計的文章」）。你需要在 `reply_content` 回覆已幫他記錄，並將提取出的具體偏好簡短寫在 `memory_to_record` 中（例如："喜歡系統設計"）。\n'
            "3. `search`：使用者**明確指定**想要尋找「特定技術主題的文章」或尋找「最近有哪些文章」（例如「幫我找找關於 AI 的新技術文章」、「最近有什麼 Rust 的文章嗎？」）。\n"
            '   - **重要限制**：只有當使用者明確提到某個具體技術名詞（如 AI, Rust, React, 系統設計 等）或明確要求搜尋特定領域時，才選擇 `search`。你需要提供對應的搜尋關鍵字並寫在 `search_query` 中（注意：**搜尋關鍵字必須是具體的技術名詞或主題**，如 "AI"、"Rust"，不能是用戶的整句閒聊或「找文章給我」這類無意義的詞）。此時 `reply_content` 應設為 null。\n\n'
            "【輸出規範】\n"
            "你必須且只能輸出一個合法的 JSON 字串，不得包含任何 Markdown 標籤（如 ```json）或多餘字元。JSON 格式必須如下：\n"
            "{\n"
            '  "thought": "你的思考鏈（中文），分析使用者的意圖與背景知識",\n'
            '  "action": "chat" | "record_preference" | "search",\n'
            '  "search_query": "如果 action 是 search，此處填入搜尋關鍵字，否則為 null",\n'
            '  "memory_to_record": "如果 action 是 record_preference，此處填入提取的偏好設定，否則為 null",\n'
            '  "reply_content": "如果 action 是 chat 或 record_preference，此處填入你的對話回覆，否則為 null"\n'
            "}"
        )

        user_prompt = f"使用者目前輸入：{query}"

        # 5. Call LLM
        try:

            async def make_api_call():
                return await self.llm_service.client.chat.completions.create(
                    model=EVAL_MODEL,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.2,  # low temp for maximum consistency in JSON output
                    max_tokens=800,
                )

            response = await self.llm_service._call_groq(
                make_api_call, context=f"agent_dispatcher(query='{query[:50]}')"
            )

            raw_content = response.choices[0].message.content
            if not raw_content:
                raise ValueError("Empty response from Groq")

            # Clean potential markdown fences
            cleaned_content = raw_content.strip()
            if cleaned_content.startswith("```"):
                cleaned_content = re.sub(r"^```[a-zA-Z]*\s*", "", cleaned_content)
                cleaned_content = re.sub(r"\s*```$", "", cleaned_content)
            cleaned_content = cleaned_content.strip()

            parsed = json.loads(cleaned_content)
            logger.info(f"Dispatcher successfully routed query with action={parsed.get('action')}")
            return parsed

        except Exception as e:
            logger.error(
                f"Dispatcher failed to process or parse response: {e}. Raw content was: {locals().get('raw_content')}"
            )
            # Safe fallback
            return {
                "thought": "Fallback to basic chat due to parsing or API error.",
                "action": "chat",
                "search_query": None,
                "memory_to_record": None,
                "reply_content": "你好！我是你的個人技術新聞助理。很高興與你交流！今天想看什麼方面的技術文章，或者有什麼技術偏好想跟我說嗎？",
            }
