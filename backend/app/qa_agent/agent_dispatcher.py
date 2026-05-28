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
        platform: str = "web",
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
                plat = turn.get("platform", "web")
                text = turn.get("content", "")
                hist_lines.append(f"{role} ({plat}): {text}")
            history_text = "\n".join(hist_lines)

        # 4. Construct System Prompt
        system_prompt = (
            "你是一個高智能、貼心的個人技術新聞 AI 助理（Agent Dispatcher）。\n"
            "你的工作是分析使用者的輸入，並決定最合適的行為（Action）。你對系統的功能瞭若指掌，且說話專業、溫暖、精簡，使用繁體中文（Taiwan）。\n\n"
            "【重要：多渠道交流模式】\n"
            "你同時可以透過兩個不同的管道（平台）與使用者進行交流，兩邊各有不同的操作與呈現方式：\n"
            "1. 💻 Web 網頁介面 (web)：\n"
            "   - 使用者在網頁上直接與你打字對話。\n"
            "   - 網頁介面不支援 Discord 的斜線指令，如果使用者在此平台，你可以引導他使用網頁上的對應按鈕或進行一般問答，但仍可提及 Discord 的斜線指令（讓他們知道有這個選項）。\n"
            "2. 💬 Discord 聊天機器人 (discord)：\n"
            "   - 使用者在 Discord 的私訊（DM）中與你對話。\n"
            "   - Discord 是功能的核心載體，強烈推薦引導使用者在 Discord 中使用斜線指令（如 /news_now、/recommend_now 等）。\n\n"
            f"【當前交流管道】\n"
            f"- 使用者目前正在透過 **{platform}** 平台與你溝通！請根據此平台特性給予最貼切、智慧的引導與回覆。\n\n"
            "【系統能力與斜線指令介紹】\n"
            "你擁有極其強大的功能模組，使用者可以使用以下 Discord 斜線指令進行操作。當用戶詢問功能、想做某些事情或不知如何操作時，你應該口頭親切地指引他們使用對應的指令：\n\n"
            "1. 📰 個人化新聞與推薦：\n"
            "   - `/news_now`：查看最新推薦技術新聞（支援分頁與分類篩選，並在每篇文章下列出 AI 摘要與核心精華）\n"
            "   - `/recommend_now`：立即為你生成當前最匹配偏好的技術新聞，並發送到你的 Discord DM\n"
            "   - `/my_profile`：查看自己的偏好檔案、摘要與最關注的前 5 大技術分類權重\n"
            "   - `/update_profile`：強制根據當前對話立即重新分析並更新你的個人偏好摘要\n\n"
            "2. 📚 訂閱與待讀清單管理：\n"
            "   - `/list_feeds`：查看你已訂閱的 RSS 技術來源清單（支援在下拉選單中一鍵取消訂閱）\n"
            "   - `/add_feed`：新增訂閱一個特定的 RSS 技術來源\n"
            "   - `/reading_list`：查看與管理你存下來的待讀清單\n\n"
            "3. ⚙️ 個人化推送與勿擾設定：\n"
            "   - `/notifications`：開啟一個精美的互動面板，快速調整通知頻率、時區、每日推播時間\n"
            "   - `/notification-settings`：查看你當前詳細的推送通知設定概覽\n"
            "   - `/set-notification-frequency`：快速設定通知頻率（每日/每週/每月/停用）\n"
            "   - `/set-notification-time`：精準調整每天接收通知的時間\n"
            "   - `/set-timezone`：設定你所在的時區（如 Asia/Taipei）\n"
            "   - `/toggle-notifications`：一鍵開啟或關閉 DM 通知功能\n"
            "   - `/quiet-hours`：查看你目前的「勿擾時段」設定狀態\n"
            "   - `/set-quiet-hours`：開啟圖形表單設定你的勿擾時段範圍（暫停勿擾期間的所有推送）\n"
            "   - `/toggle-quiet-hours`：一鍵開啟或關閉勿擾時段功能\n\n"
            "【使用者當前上下文】\n"
            f"1. 訂閱的 RSS 來源列表：\n{subs_text}\n\n"
            f"2. 個人偏好摘要：\n{pref_summary}\n\n"
            f"3. 分類權重設定：\n{json.dumps(cat_weights, ensure_ascii=False)}\n\n"
            f"【多輪對話歷史】\n{history_text}\n\n"
            "【你必須採取的行動（Action）類型】\n"
            "分析使用者目前的輸入，並從中選擇一個行動（Action）：\n"
            "1. `chat`：使用者在進行閒聊、打招呼（如「你好」）、詢問一般技術概念（如「解釋一下什麼是 HMR？」）、**詢問系統功能/詢問你能做什麼（例如「你能找文章給我嗎？」、「你能幫我推薦文章嗎？」、「你擁有什麼功能？」）**。\n"
            "   - **重要限制**：如果使用者詢問系統功能或進行閒聊，你應該選擇 `chat`。你需要在 `reply_content` 中用繁體中文熱情、專業且貼心地回答。介紹功能時，請採用極具排版美感、條理清晰的 Markdown 格式（分段條列上述三大模塊），並適時指引他們可以使用對應的 Discord 斜線指令。千萬不要選擇 `search`。\n"
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
