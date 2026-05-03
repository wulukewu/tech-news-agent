-- 檢查現有資料表的 SQL
-- 在 Supabase SQL Editor 執行這個來檢查你的資料庫狀態

-- 檢查所有資料表
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

-- 檢查 users 資料表是否存在
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'users' AND table_schema = 'public'
ORDER BY ordinal_position;

-- 檢查 pgvector 擴充功能
SELECT extname, extversion
FROM pg_extension
WHERE extname = 'vector';
