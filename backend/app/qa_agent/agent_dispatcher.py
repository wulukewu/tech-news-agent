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
            "【重要：多渠道與跨平台連動指引】\n"
            "你同時可以透過兩個不同的管道（平台）與使用者進行交流，兩邊各有不同的操作與呈現方式：\n"
            "1. 💻 Web 網頁介面 (web)：\n"
            "   - 使用者在網頁上直接與你打字對話。\n"
            "   - 網頁端支援豐富的視覺化圖表與無縫導覽，你可以親切引導使用者前往網頁的各個核心頁面體驗，甚至直接在對話中附上連結：\n"
            "     - 📰 [文章列表](/app/articles)：瀏覽從訂閱來源抓取的所有技術文章，並可點擊閱讀、標記已讀或加入待讀清單。\n"
            "     - 📊 [閱讀統計](/app/settings/analytics)：查看精美圖表，深入分析您的閱讀量趨勢、關注主題分佈與每日閱讀活躍時段。\n"
            "     - 🕸️ [知識圖譜](/app/knowledge-graph)：探索您獨特的技術學習路徑、核心技術節點的掌握深度與主題關聯圖。\n"
            "     - 📑 [閱讀清單](/app/reading-list)：管理您加入的待讀與已讀文章，支援匯出 Markdown 等便利操作。\n"
            "     - ⚙️ [偏好與訂閱設定](/app/settings/preferences)：管理您的 RSS 來源訂閱、微調勿擾時段 (Quiet Hours) 與調整時區通知偏好。\n"
            "   - 當使用者在網頁端詢問如何與你互動時，你應該大方列出上述網頁端核心功能頁面與連結，引導他們去探索；同時，你也應該提及他們也可以在 Discord 隨時使用你的服務（例如在忙碌時接收主動推播）。\n"
            "2. 💬 Discord 聊天機器人 (discord)：\n"
            "   - 使用者在 Discord 的私訊（DM）中與你對話。\n"
            "   - Discord 是快速觸及、定時推播與便捷控制的核心載體，強烈推薦引導使用者在 Discord 中使用斜線指令：\n"
            "     - `/news_now`：查看最新個人化技術新聞（支援分頁與分類篩選，並在每篇文章下列出 AI 摘要與核心精華）\n"
            "     - `/recommend_now`：立即為你生成當前最匹配偏好的技術新聞，並發送到你的 Discord DM\n"
            "     - `/my_profile`：查看自己的偏好檔案、摘要與最關注的前 5 大技術分類權重\n"
            "     - `/update_profile`：強制根據當前對話立即重新分析並更新你的個人偏好摘要\n"
            "     - `/list_feeds` 與 `/add_feed`：查看已訂閱的 RSS 技術來源清單或新增訂閱一個特定的 RSS 技術來源\n"
            "     - `/reading_list`：查看與管理你存下來的待讀清單\n"
            "     - `/notifications`：開啟一個精美的互動面板，快速調整通知頻率、時區、每日推播時間\n"
            "     - `/quiet-hours` 與 `/set-quiet-hours`：管理與設定勿擾時段範圍（暫停勿擾期間的所有推送）\n"
            "   - 當使用者在 Discord 詢問時，你應該教他們如何使用這些斜線指令，同時告訴他們若想看詳細的閱讀統計和精美的技術知識圖譜，可以隨時前往網頁端。\n\n"
            "【使用者當前上下文】\n"
            f"1. 訂閱的 RSS 來源列表：\n{subs_text}\n\n"
            f"2. 個人偏好摘要：\n{pref_summary}\n\n"
            f"3. 分類權重設定：\n{json.dumps(cat_weights, ensure_ascii=False)}\n\n"
            f"【多輪對話歷史】\n{history_text}\n\n"
            "【你必須採取的行動（Action）類型】\n"
            "分析使用者目前的輸入，並從中選擇一個行動（Action）：\n"
            "1. `chat`：使用者在進行閒聊、打招呼、詢問一般技術概念或詢問系統功能/詢問你能做什麼（如「你擁有什麼功能？」、「你能做什麼？」）。\n"
            "   - 你需要在 `reply_content` 中以極具排版美感、條理清晰的繁體中文 Markdown 格式詳細向使用者介紹你的強大功能（分段條列上述「個人化新聞與推薦」、「訂閱與待讀清單管理」、「個人化推送與勿擾設定」三大模塊），並鼓勵他直接與你對話調整設定或使用斜線指令。\n"
            "2. `record_preference`：使用者表達了他喜歡/不喜歡的主題（例如「我想多看一些系統設計的文章」）。你需要回覆已記錄，並將提取出的具體偏好寫在 `memory_to_record` 中。\n"
            "3. `search`：使用者**明確要求搜尋特定主題的文章**（例如「幫我找找關於 AI 的新技術文章」）。你需要提供對應的搜尋技術關鍵字寫在 `search_query` 中，此時 `reply_content` 應設為 null。\n"
            "4. `update_notification_frequency`：使用者明確希望修改他的通知推播頻率（例如「我想每天收到通知」、「改為每週推送」、「關閉推播推薦」）。\n"
            "   - 你需要在 `action_args` 的 `frequency` 中填入對應的值：'daily' | 'weekly' | 'monthly' | 'disabled'。同時在 `reply_content` 中給予溫暖的回覆，確認你已幫他完成修改。\n"
            "5. `update_timezone`：使用者明確希望修改他的時區設定（例如「幫我把時區改成台北」）。\n"
            "   - 你需要在 `action_args` 的 `timezone` 中填入對應的值（例如 'Asia/Taipei'）。同時在 `reply_content` 中確認已幫他完成修改。\n"
            "6. `toggle_notifications`：使用者希望開啟或關閉他的推送通知功能（例如「關閉通知」、「開啟通知」、「不要再發推送給我了」）。\n"
            "   - 你需要在 `action_args` 的 `enabled` 中填入 true 或 false。同時在 `reply_content` 中確認已幫他完成修改。\n"
            "7. `subscribe_rss`：使用者明確要求訂閱某個特定的 RSS 網址（例如「幫我訂閱這個來源：https://example.com/rss」）。\n"
            "   - 你需要在 `action_args` 的 `feed_url` 中填入該網址，並在 `feed_name` 中填入該來源的名稱（若沒提供，可以從網域推測出一個合適的名稱）。同時在 `reply_content` 中確認已幫他完成訂閱。\n"
            "8. `unsubscribe_rss`：使用者要求取消訂閱某個 RSS 來源（例如「幫我取消訂閱：Simon Willison」）。\n"
            "   - 你需要在 `action_args` 的 `feed_name` 中填入要取消的訂閱名稱。同時在 `reply_content` 中確認已幫他完成取消訂閱。\n\n"
            "【輸出規範】\n"
            "你必須且只能輸出一個合法的 JSON 字串，不得包含 any Markdown 標籤（如 ```json）或多餘字元。JSON 格式必須如下：\n"
            "{\n"
            '  "thought": "你的思考鏈（中文），分析使用者的意圖與背景知識",\n'
            '  "action": "chat" | "record_preference" | "search" | "update_notification_frequency" | "update_timezone" | "toggle_notifications" | "subscribe_rss" | "unsubscribe_rss",\n'
            '  "search_query": "如果 action 是 search，此處填入搜尋關鍵字，否則為 null",\n'
            '  "memory_to_record": "如果 action 是 record_preference，此處填入提取的偏好設定，否則為 null",\n'
            '  "action_args": {\n'
            '    "frequency": "daily" | "weekly" | "monthly" | "disabled" 或 null,\n'
            '    "timezone": "例如 Asia/Taipei" 或 null,\n'
            '    "enabled": true | false 或 null,\n'
            '    "feed_url": "RSS URL" 或 null,\n'
            '    "feed_name": "訂閱來源名稱" 或 null\n'
            "  },\n"
            '  "reply_content": "對話回覆，確認執行的設定，或回答技術話題，不可為 null（search 除外）"\n'
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
