-- Knowledge Graph Agent Database Schema

-- Technical domains (e.g., Kubernetes, React, Python)
CREATE TABLE IF NOT EXISTS technical_domains (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    is_builtin BOOLEAN DEFAULT false,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge nodes (individual concepts/skills within a domain)
CREATE TABLE IF NOT EXISTS knowledge_nodes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    domain_id UUID NOT NULL REFERENCES technical_domains(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    display_name VARCHAR(300) NOT NULL,
    description TEXT,
    difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 5),
    estimated_hours FLOAT DEFAULT 1.0,
    tags TEXT[] DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(domain_id, name)
);

-- Dependency edges between nodes
CREATE TABLE IF NOT EXISTS node_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    dependency_type VARCHAR(50) NOT NULL DEFAULT 'prerequisite'
        CHECK (dependency_type IN ('prerequisite', 'related', 'extends')),
    confidence_score FLOAT NOT NULL DEFAULT 1.0 CHECK (confidence_score BETWEEN 0 AND 1),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_node_id, target_node_id, dependency_type)
);

-- User progress per node
CREATE TABLE IF NOT EXISTS user_node_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    node_id UUID NOT NULL REFERENCES knowledge_nodes(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'not_started'
        CHECK (status IN ('not_started', 'in_progress', 'completed')),
    completed_at TIMESTAMPTZ,
    time_spent_minutes INTEGER DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, node_id)
);

-- User achievements
CREATE TABLE IF NOT EXISTS user_achievements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    domain_id UUID NOT NULL REFERENCES technical_domains(id) ON DELETE CASCADE,
    badge_type VARCHAR(50) NOT NULL,
    badge_name VARCHAR(200) NOT NULL,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, domain_id, badge_type)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_nodes_domain ON knowledge_nodes(domain_id);
CREATE INDEX IF NOT EXISTS idx_node_dependencies_source ON node_dependencies(source_node_id);
CREATE INDEX IF NOT EXISTS idx_node_dependencies_target ON node_dependencies(target_node_id);
CREATE INDEX IF NOT EXISTS idx_user_node_progress_user ON user_node_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_user_node_progress_node ON user_node_progress(node_id);
CREATE INDEX IF NOT EXISTS idx_user_achievements_user ON user_achievements(user_id);

-- Seed built-in domains
INSERT INTO technical_domains (name, display_name, description, icon, is_builtin) VALUES
    ('kubernetes', 'Kubernetes', 'Container orchestration platform', '⚙️', true),
    ('react', 'React', 'JavaScript UI library', '⚛️', true),
    ('python', 'Python', 'General-purpose programming language', '🐍', true),
    ('machine-learning', 'Machine Learning', 'ML algorithms and techniques', '🤖', true),
    ('devops', 'DevOps', 'Development and operations practices', '🔄', true),
    ('typescript', 'TypeScript', 'Typed JavaScript superset', '📘', true),
    ('docker', 'Docker', 'Container platform', '🐳', true),
    ('rust', 'Rust', 'Systems programming language', '🦀', true),
    ('golang', 'Go', 'Concurrent systems language', '🐹', true),
    ('nextjs', 'Next.js', 'React framework for production', '▲', true)
ON CONFLICT (name) DO NOTHING;
