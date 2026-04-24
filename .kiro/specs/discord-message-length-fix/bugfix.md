# Bugfix Requirements Document

## Introduction

The `/news_now` Discord bot command has two formatting bugs when delivering the LLM-generated newsletter to Discord:

1. **訊息截斷**：LLM 生成的電子報草稿可能超過 Discord 的 2000 字元硬性限制，導致 `discord.errors.HTTPException: 400 Bad Request`，訊息完全無法送達。

2. **連結格式異常**：LLM 生成的 Markdown 中，每篇文章的推薦說明項目（`💡 推薦原因`、`🎯 行動價值`、`🛠️ 折騰指數`）緊接在超連結後面，沒有換行，且使用 `+` 符號作為列表標記，導致 Discord 顯示時連結文字與加號混在一起，格式完全錯亂。

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN the LLM-generated newsletter draft exceeds 2000 characters THEN the system raises a `discord.errors.HTTPException: 400 Bad Request` and the message is never delivered to Discord.

1.2 WHEN the draft exceeds 2000 characters THEN the system logs an unhandled error and the Discord interaction ends without any meaningful feedback to the user.

1.3 WHEN the LLM generates article metadata items (推薦原因、行動價值、折騰指數) after a Markdown hyperlink THEN the system renders them without a preceding newline, causing the `+` list markers to appear concatenated directly after the link URL in Discord.

1.4 WHEN the LLM uses `+` as a Markdown list marker for article metadata items THEN the system displays them as inline text appended to the previous line rather than as separate list items, because Discord's Markdown renderer does not treat `+` as a list marker.

### Expected Behavior (Correct)

2.1 WHEN the LLM-generated newsletter draft exceeds 2000 characters THEN the system SHALL truncate or split the content so that each Discord message send call receives 2000 or fewer characters.

2.2 WHEN the draft exceeds 2000 characters THEN the system SHALL successfully deliver the full or truncated newsletter content to the Discord channel without raising an HTTP error.

2.3 WHEN the LLM generates article metadata items after a Markdown hyperlink THEN the system SHALL ensure each metadata item appears on its own line, separated from the hyperlink by a newline.

2.4 WHEN article metadata items use `+` as a list marker THEN the system SHALL replace `+` list markers with `-` or `*` so that Discord's Markdown renderer correctly displays them as separate list items.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN the LLM-generated newsletter draft is 2000 characters or fewer THEN the system SHALL CONTINUE TO send the message in a single `followup.send` call without modification to the overall content structure.

3.2 WHEN the `/news_now` command is executed THEN the system SHALL CONTINUE TO attach the interactive button view to the Discord message response.

3.3 WHEN the `/news_now` command encounters any other error (e.g., no feeds, no articles, LLM failure) THEN the system SHALL CONTINUE TO return the appropriate error or informational message to the user.

3.4 WHEN the newsletter draft contains properly formatted Markdown hyperlinks (e.g., `[title](url)`) THEN the system SHALL CONTINUE TO preserve the hyperlink syntax so Discord renders them as clickable links.
