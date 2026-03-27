-- 1. 时区和编码设置
SET client_encoding = 'UTF8';
SET TIME ZONE 'UTC';
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 修复 users 表缺失列
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
UPDATE users SET updated_at = created_at WHERE updated_at IS NULL;

-- 角色表 (支持继承)
CREATE TABLE IF NOT EXISTS roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    parent_id INTEGER REFERENCES roles(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 修复 roles 表缺失列
ALTER TABLE roles ADD COLUMN IF NOT EXISTS parent_id INTEGER;
ALTER TABLE roles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
UPDATE roles SET updated_at = created_at WHERE updated_at IS NULL;

-- 用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, role_id)
);

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description VARCHAR(255),
    resource VARCHAR(100) NOT NULL,
    action VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 修复 permissions 表缺失列
ALTER TABLE permissions ADD COLUMN IF NOT EXISTS resource VARCHAR(100);
ALTER TABLE permissions ADD COLUMN IF NOT EXISTS action VARCHAR(50);
ALTER TABLE permissions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP;
UPDATE permissions SET updated_at = created_at WHERE updated_at IS NULL;
-- 为旧权限数据设置默认 resource 和 action
UPDATE permissions SET resource = SPLIT_PART(name, ':', 1), action = SPLIT_PART(name, ':', 2) WHERE resource IS NULL OR action IS NULL;

-- 角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY (role_id, permission_id)
);

-- 手机验证码表
CREATE TABLE IF NOT EXISTS sms_verifications (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) NOT NULL,
    code VARCHAR(10) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 修复 sms_verifications 表缺失列
ALTER TABLE sms_verifications ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE sms_verifications ADD COLUMN IF NOT EXISTS is_used BOOLEAN DEFAULT FALSE;

-- 用户详情表
CREATE TABLE IF NOT EXISTS user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE NOT NULL,
    avatar_url VARCHAR(255),
    education VARCHAR(100),
    target_position VARCHAR(100),
    work_years INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 消息通知表
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 知识图谱 (技能树)
CREATE TABLE IF NOT EXISTS knowledge_graphs (
    id SERIAL PRIMARY KEY,
    concept_name VARCHAR(100) NOT NULL,
    description TEXT,
    parent_id INTEGER REFERENCES knowledge_graphs(id) ON DELETE SET NULL,
    tags JSONB DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 岗位表
CREATE TABLE IF NOT EXISTS job_positions (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    level VARCHAR(50),
    industry VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 岗位与技能关联表
CREATE TABLE IF NOT EXISTS job_skills (
    job_position_id INTEGER REFERENCES job_positions(id) ON DELETE CASCADE,
    knowledge_graph_id INTEGER REFERENCES knowledge_graphs(id) ON DELETE CASCADE,
    weight DOUBLE PRECISION DEFAULT 1.0,
    PRIMARY KEY (job_position_id, knowledge_graph_id)
);

-- 测评试卷
CREATE TABLE IF NOT EXISTS assessments (
    id SERIAL PRIMARY KEY,
    title VARCHAR(100) NOT NULL,
    description TEXT,
    job_position_id INTEGER REFERENCES job_positions(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 测评题目
CREATE TABLE IF NOT EXISTS questions (
    id SERIAL PRIMARY KEY,
    assessment_id INTEGER REFERENCES assessments(id) ON DELETE CASCADE NOT NULL,
    knowledge_graph_id INTEGER REFERENCES knowledge_graphs(id) ON DELETE SET NULL,
    question_type VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    options JSONB DEFAULT '[]',
    correct_answer JSONB NOT NULL,
    score_weight DOUBLE PRECISION DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户测评记录
CREATE TABLE IF NOT EXISTS user_assessment_records (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    assessment_id INTEGER REFERENCES assessments(id) ON DELETE CASCADE NOT NULL,
    total_score DOUBLE PRECISION DEFAULT 0.0,
    details JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 用户技能掌握度
CREATE TABLE IF NOT EXISTS user_skill_mastery (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE NOT NULL,
    knowledge_graph_id INTEGER REFERENCES knowledge_graphs(id) ON DELETE CASCADE NOT NULL,
    mastery_level DOUBLE PRECISION DEFAULT 0.0,
    last_assessed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, knowledge_graph_id)
);

-- 3. 索引创建 (使用 IF NOT EXISTS 避免重复创建报错)
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);
CREATE INDEX IF NOT EXISTS idx_roles_parent ON roles(parent_id);
CREATE INDEX IF NOT EXISTS idx_permissions_name ON permissions(name);
CREATE INDEX IF NOT EXISTS idx_permissions_resource ON permissions(resource);
CREATE INDEX IF NOT EXISTS idx_sms_verifications_phone ON sms_verifications(phone);
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);

-- 4. 初始数据插入

-- 插入基础权限 (先清理旧数据避免冲突)
INSERT INTO permissions (name, description, resource, action) VALUES 
('user:read', '查看用户', 'user', 'read'),
('user:create', '创建用户', 'user', 'create'),
('user:update', '更新用户', 'user', 'update'),
('user:delete', '删除用户', 'user', 'delete'),
('role:read', '查看角色', 'role', 'read'),
('role:create', '创建角色', 'role', 'create'),
('role:update', '更新角色', 'role', 'update'),
('role:delete', '删除角色', 'role', 'delete')
ON CONFLICT (name) DO NOTHING;

-- 插入默认管理员角色
INSERT INTO roles (name, description) VALUES 
('admin', '系统管理员')
ON CONFLICT (name) DO NOTHING;

-- 为管理员角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT r.id, p.id 
FROM roles r, permissions p 
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- 插入默认超级管理员账号 (密码: Admin@123456)
-- bcrypt hash of Admin@123456
INSERT INTO users (username, email, phone, hashed_password) VALUES 
('admin', 'admin@example.com', '13800138000', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjIoIQ/wK2')
ON CONFLICT (username) DO NOTHING;

-- 分配超级管理员角色
INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'admin' AND r.name = 'admin'
ON CONFLICT DO NOTHING;