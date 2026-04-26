-- Learning Path Planning Agent Database Schema
-- Requirements: 10.1, 10.2

-- 用戶學習目標
CREATE TABLE learning_goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_skill VARCHAR(100) NOT NULL,
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5) DEFAULT 1,
    estimated_hours INTEGER DEFAULT 0,
    status VARCHAR(20) CHECK (status IN ('active', 'completed', 'paused', 'cancelled')) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 生成的學習路徑
CREATE TABLE learning_paths (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES learning_goals(id) ON DELETE CASCADE,
    path_data JSONB NOT NULL, -- 儲存完整的路徑結構
    total_stages INTEGER DEFAULT 3,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 路徑中的各階段
CREATE TABLE learning_stages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    path_id UUID NOT NULL REFERENCES learning_paths(id) ON DELETE CASCADE,
    stage_order INTEGER NOT NULL,
    stage_name VARCHAR(100) NOT NULL, -- 'foundation', 'intermediate', 'advanced'
    stage_description TEXT,
    estimated_hours INTEGER DEFAULT 0,
    prerequisites TEXT[], -- 前置技能要求
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 用戶進度記錄
CREATE TABLE learning_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    goal_id UUID NOT NULL REFERENCES learning_goals(id) ON DELETE CASCADE,
    stage_id UUID REFERENCES learning_stages(id) ON DELETE CASCADE,
    article_id UUID REFERENCES articles(id) ON DELETE CASCADE,
    status VARCHAR(20) CHECK (status IN ('not_started', 'in_progress', 'completed', 'skipped')) DEFAULT 'not_started',
    completion_percentage INTEGER CHECK (completion_percentage BETWEEN 0 AND 100) DEFAULT 0,
    time_spent_minutes INTEGER DEFAULT 0,
    notes TEXT,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 技能依賴關係樹
CREATE TABLE skill_tree (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    skill_name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100), -- 'frontend', 'backend', 'devops', 'data', etc.
    difficulty_level INTEGER CHECK (difficulty_level BETWEEN 1 AND 5) DEFAULT 1,
    estimated_hours INTEGER DEFAULT 0,
    prerequisites VARCHAR(100)[], -- 前置技能名稱陣列
    tags VARCHAR(50)[],
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 建立索引以提升查詢效能
CREATE INDEX idx_learning_goals_user_id ON learning_goals(user_id);
CREATE INDEX idx_learning_goals_status ON learning_goals(status);
CREATE INDEX idx_learning_paths_goal_id ON learning_paths(goal_id);
CREATE INDEX idx_learning_stages_path_id ON learning_stages(path_id);
CREATE INDEX idx_learning_stages_order ON learning_stages(stage_order);
CREATE INDEX idx_learning_progress_user_id ON learning_progress(user_id);
CREATE INDEX idx_learning_progress_goal_id ON learning_progress(goal_id);
CREATE INDEX idx_learning_progress_status ON learning_progress(status);
CREATE INDEX idx_skill_tree_category ON skill_tree(category);
CREATE INDEX idx_skill_tree_difficulty ON skill_tree(difficulty_level);

-- 建立觸發器以自動更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_learning_goals_updated_at BEFORE UPDATE ON learning_goals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_learning_paths_updated_at BEFORE UPDATE ON learning_paths FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_learning_progress_updated_at BEFORE UPDATE ON learning_progress FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_skill_tree_updated_at BEFORE UPDATE ON skill_tree FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
