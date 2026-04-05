# Tech News Agent - Web Dashboard Frontend

這是 Tech News Agent 專案的 Web 前端應用，使用 Next.js 14+ 建立。

## 技術棧

- **框架**: Next.js 14+ (App Router)
- **語言**: TypeScript 5+
- **樣式**: TailwindCSS 3+
- **UI 元件**: shadcn/ui (基於 Radix UI)
- **狀態管理**: React Context API

## 開發環境設置

### 前置需求

- Node.js 20+
- npm 或 yarn

### 安裝依賴

```bash
npm install
```

### 環境變數配置

複製 `.env.example` 到 `.env.local` 並配置環境變數：

```bash
cp .env.example .env.local
```

編輯 `.env.local`：

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 啟動開發伺服器

```bash
npm run dev
```

應用將在 http://localhost:3000 啟動。

## 專案結構

```
frontend/
├── app/                    # Next.js App Router 頁面
│   ├── layout.tsx         # Root Layout
│   ├── page.tsx           # 首頁
│   └── globals.css        # 全域樣式
├── components/            # React 元件
│   └── ui/               # shadcn/ui 元件
├── lib/                   # 工具函式和 API 客戶端
│   └── utils.ts          # 通用工具函式
├── types/                 # TypeScript 型別定義
├── contexts/              # React Context 提供者
├── public/                # 靜態資源
└── package.json           # 專案依賴
```

## 可用指令

- `npm run dev` - 啟動開發伺服器
- `npm run build` - 建立生產版本
- `npm run start` - 啟動生產伺服器
- `npm run lint` - 執行 ESLint 檢查
- `npm run type-check` - 執行 TypeScript 型別檢查

## Docker 部署

使用 Docker Compose 部署：

```bash
# 從專案根目錄執行
docker-compose up -d frontend
```

或單獨建立 Docker 映像：

```bash
docker build -t tech-news-agent-frontend .
docker run -p 3000:3000 tech-news-agent-frontend
```

## 開發指南

### 添加 shadcn/ui 元件

使用 shadcn/ui CLI 添加元件：

```bash
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
```

### API 整合

API 客戶端將在 `lib/api/` 目錄中實作，用於與 FastAPI 後端通訊。

### 認證流程

應用使用 Discord OAuth2 進行認證，JWT Token 儲存在 HttpOnly Cookie 中。

## 授權

此專案為私有專案。
