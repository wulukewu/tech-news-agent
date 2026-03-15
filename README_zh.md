# Tech News Agent

這是一個結合了 FastAPI、Discord Bot 與 Groq LLM 的自動化技術資訊策展助理。它能自動從 Notion 讀取 RSS 來源，每週抓取、評分技術文章，並透過 Discord 推播精美的 Markdown 電子報。

## 核心功能

- 自動化抓取：每週五 17:00 自動從 Notion 取得 RSS 訂閱源並抓取文章。
- 硬核評分：使用 Groq (Llama 3.1 8B) 進行技術價值與「折騰指數」評估。
- 精選報表：自動過濾行銷廢話，並由 Llama 3.3 70B 產出極客風格的電子報。
- 雙向互動：支援 Discord 斜線指令 (/news_now) 與按鈕互動（點擊直接存入 Notion 稍後閱讀）。

---

## 前置準備

### 1. Notion 資料庫設定

你需要建立兩個資料庫，並將 Notion Integration (Connect) 加入權限。

> ⚠️ 欄位名稱區分大小寫，必須與下表完全一致。

**Feeds 資料庫**（儲存 RSS 訂閱源）：

| 欄位名稱   | 類型     | 備註                      |
| ---------- | -------- | ------------------------- |
| `Name`     | Title    | 預設標題欄，保持原名即可  |
| `URL`      | URL      |                           |
| `Category` | Select   | 例如 DevOps、AI、Security |
| `Active`   | Checkbox | 只有勾選的項目才會被抓取  |

**Read Later 資料庫**（透過 Discord 按鈕儲存文章）：

| 欄位名稱          | 類型   | 備註                             |
| ----------------- | ------ | -------------------------------- |
| `Title`           | Title  | 將預設的「Name」欄位改名為此     |
| `URL`             | URL    |                                  |
| `Added_At`        | Date   |                                  |
| `Source_Category` | Select |                                  |
| `Status`          | Status | 必須包含一個名為 `Unread` 的選項 |

### 2. Discord Bot 設定

- 至 Discord Developer Portal 建立 Bot。
- 務必開啟 Message Content Intent。
- 取得 Token 並將 Bot 加入你的伺服器。
- 取得要推播的 Channel ID。

### 3. API Key

- 取得 Groq Cloud 的 API Key。

---

## 如何運行

### 方法一：使用 Docker (推薦，適合 NAS 或伺服器)

1.  複製並設定環境變數：

    ```bash
    cp .env.example .env
    ```

    編輯 .env 並填入你的所有 Token 與 ID。

2.  啟動服務：
    ```bash
    docker compose up -d
    ```

### 方法二：本地 Python 運行

1.  安裝依賴：

    ```bash
    pip install -r requirements.txt
    ```

2.  設定環境變數 (建立 .env)。

3.  啟動應用程式：
    ```bash
    python -m app.main
    ```

---

## Discord 指令

- /news_now：立即觸發本週的技術新聞抓取與生成。
- /add_feed：(開發中) 快速將 RSS 加入 Notion。

## 專案架構

```text
tech-news-agent/
├── app/
│   ├── main.py          # FastAPI 進入點與生命週期管理
│   ├── bot/             # Discord Bot 相關邏輯
│   ├── services/        # 核心服務 (Notion, RSS, LLM)
│   ├── schemas/         # Pydantic 資料結構
│   └── tasks/           # APScheduler 排程任務
└── ...
```
