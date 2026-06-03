# Mock 数据迁移至后端数据库方案

> 生成时间：2026-06-03
> 最后更新：2026-06-03
> 前端仓库：MianMianMaster (Vue 3 + Vite + TypeScript)
> 后端技术栈：FastAPI + SQLAlchemy + PostgreSQL + Alembic (独立仓库)

## 当前进度

| 阶段 | 状态 | 完成时间 |
|------|------|----------|
| Phase 1: 数据提取 | ✅ 已完成 | 2026-06-03 |
| Phase 2: Seed 脚本 | ⏳ 待后端团队执行 | - |
| Phase 3: 前端清理 | ⏳ 待 Phase 2 完成后执行 | - |

---

## 一、现状分析

### 1.1 Mock 数据分布

| 层级 | 位置 | 数量 | 说明 |
|------|------|------|------|
| **正式 Mock 文件** | `src/mock/data/*.mock.ts` | 9 个文件 | 类型安全，结构化数据，直接对应后端 API |
| **Store 降级数据** | `src/stores/user.ts` / `learning.ts` | 2 个 Store | API 失败时的 fallback |
| **组件内联硬编码** | `src/views/*.vue` | 9 个视图 | 未经提取的占位数据 |
| **SSE Mock** | `src/mock/plugins/` | 1 个插件 | 流式面试对话模拟数据 |

### 1.2 正式 Mock 数据清单（`src/mock/data/`）

| 文件 | 导出变量 | 数据量 | 对应后端模块 |
|------|----------|--------|-------------|
| `user.mock.ts` | mockUser | 1 条 | `/user` |
| | mockInterviewHistory | 12 条 | `/interview` |
| | mockAbilityData | 4 种职位 | `/user` (能力评估) |
| | mockGameInterviewData | 关卡+成就+排行 | `/interview` (游戏化) |
| | mockResumeData | 1 份简历 | `/user` (简历) |
| | mockResumeDiagnosisResult | 1 份诊断 | `/user` (简历诊断) |
| `interview.mock.ts` | mockInterviewSessions | 3 条 | `/interview` |
| | mockInterviewReport | 1 条 | `/interview` |
| | mockGameLevels | 5 条 | `/interview` (游戏化) |
| | mockGameStats | 1 条 | `/interview` (游戏化) |
| | mockGameAchievements | 5 条 | `/interview` (游戏化) |
| | mockLeaderboard | 5 条 | `/interview` (游戏化) |
| `community.mock.ts` | mockPosts | 7 条 | `/community` |
| | mockComments | 2 篇帖的评论 | `/community` |
| | mockHotTopics | 4 条 | `/community` |
| | mockActiveUsers | 4 条 | `/community` / `/user` |
| `learning.mock.ts` | mockCourses | 4 条 | `/learning` |
| | mockCollections | 3 条 | `/learning` |
| | mockWrongQuestions | 5 条 | `/learning` |
| | mockBadges | 5 条 | `/learning` |
| | mockUserBadges | 3 条 | `/learning` |
| `assessment.mock.ts` | mockAssessments | 3 条 | `/assessments` |
| | mockAssessmentResults | 3 条 | `/assessments` |
| `auth.mock.ts` | mockToken | 1 条 | `/auth` (不入库) |
| | mockLoginResponse | 1 条 | `/auth` (不入库) |
| | mockRegisterUser | 1 条 | `/auth` → `/user` |
| `notification.mock.ts` | mockNotifications | 5 条 | `/notifications` |
| | mockNotificationPreferences | 1 条 | `/notifications` |
| `job.mock.ts` | mockJobPositions | 5 条 | `/jobs` |
| | mockSkillTree | 1 棵技能树 | `/jobs` |
| | mockJobMatchResults | 5 条 | `/jobs` |
| `system.mock.ts` | mockSystemConfigs | 3 条 | `/system` |
| | mockSystemHealth | 1 条 | `/system` (运行时，不入库) |
| | mockSystemAnnouncements | 2 条 | `/system` |

### 1.3 组件内联数据清单（需要额外处理）

| 视图文件 | 内联数据 | 数据类型 | 建议归属 |
|----------|----------|----------|----------|
| `Matching.vue` | jobMatches, hotJobs, skillRadarData | 职位匹配数据 | `/jobs` 模块 |
| `Knowledge.vue` | categories, recentTopics, hotInterviewAnalyses, resources | 知识库数据 | 新增 `/knowledge` 模块 |
| `Growth.vue` | skills, learningResources, wrongQuestions, learningPlans, jobQuestionBanks | 成长数据 | `/learning` 模块 |
| `LevelDetail.vue` | gameLevels | 游戏关卡 | `/interview` (游戏化) |
| `LevelChallenge.vue` | levels | 挑战关卡 | `/interview` (游戏化) |
| `Interview.vue` | questionBank | 面试题库 | `/interview` |
| `JobSpecificQuestionBank.vue` | jobCategories, mockQuestions | 岗位题库 | `/jobs` 或 `/interview` |
| `Home.vue` | studentFeatures, newsItems, userReviews | 首页展示 | `/system` |
| `Profile.vue` | positions | 职位选项 | `/jobs` |

---

## 二、迁移策略

### 2.1 总体思路

```
前端 Mock 数据 → 提取为 JSON → 编写 Seed 脚本 → 后端 Alembic Seed Migration → PostgreSQL
```

**核心原则：**
- Mock 数据作为**初始种子数据 (Seed Data)**，通过后端的 Alembic 迁移脚本写入数据库
- 不直接从前端导出 SQL，而是让后端团队基于 JSON 文件编写 Python seed 脚本
- 分批迁移，按模块优先级排序

### 2.2 推荐方案：后端 Alembic Seed 脚本

**选择理由：**
1. 后端已经使用 Alembic 做数据库迁移，seed 脚本是最自然的方式
2. 可以利用 SQLAlchemy ORM，确保数据与模型一致
3. 支持幂等操作（可重复执行不重复插入）
4. 可版本控制，团队协作友好

**替代方案对比：**

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| Alembic Seed Migration | 与迁移系统统一，可版本控制 | 需后端团队配合 | ⭐⭐⭐⭐⭐ |
| 独立 Python Seed 脚本 | 灵活，可独立运行 | 与迁移系统分离 | ⭐⭐⭐⭐ |
| SQL 脚本直接导入 | 简单直接 | 难维护，不跨数据库 | ⭐⭐ |
| 通过 API 批量写入 | 真实模拟用户行为 | 慢，需认证处理 | ⭐⭐ |

---

## 三、执行计划

### Phase 1：数据提取（✅ 已完成 2026-06-03）

**目标：** 将 Mock 数据导出为标准 JSON 文件，供后端消费。

**实际执行结果：**
- 导出脚本：[scripts/export-mock-data.ts](scripts/export-mock-data.ts)
- 运行命令：`npx tsx scripts/export-mock-data.ts`
- 输出目录：`docs/seed-data/`
- 导出文件数：**30 个 JSON 文件**
- 总记录数：**98 条**
- 总大小：**134 KB**

**各模块导出明细：**

| 模块 | 文件数 | 记录数 | 说明 |
|------|--------|--------|------|
| auth | 1 | 2 | users (mockUser + mockRegisterUser) |
| user | 4 | 15 | interview_history(12), ability_data(1), resume_data(1), resume_diagnosis(1) |
| interview | 7 | 21 | sessions(3), reports(1), game_levels(5), game_stats(1), achievements(5), leaderboard(5), game_interview_data(1) |
| community | 4 | 16 | posts(7), comments(1), hot_topics(4), active_users(4) |
| learning | 5 | 20 | courses(4), collections(3), wrong_questions(5), badges(5), user_badges(3) |
| assessment | 2 | 6 | assessments(3), results(3) |
| notification | 2 | 6 | notifications(5), preferences(1) |
| job | 3 | 7 | positions(5), skill_tree(1), match_results(1) |
| system | 2 | 5 | configs(3), announcements(2) |

**步骤：**

#### 1.1 创建导出脚本

在项目根目录创建 `scripts/export-mock-data.ts`：

```typescript
// scripts/export-mock-data.ts
// 运行方式: npx tsx scripts/export-mock-data.ts

import { writeFileSync, mkdirSync } from 'fs'
import { join } from 'path'

// 导入所有 mock 数据
import {
  mockUser,
  mockInterviewHistory,
  mockAbilityData,
  mockGameInterviewData,
  mockResumeData,
  mockResumeDiagnosisResult
} from '../src/mock/data/user.mock'

import {
  mockInterviewSessions,
  mockInterviewReport,
  mockGameLevels,
  mockGameStats,
  mockGameAchievements,
  mockLeaderboard
} from '../src/mock/data/interview.mock'

import {
  mockPosts,
  mockComments,
  mockHotTopics,
  mockActiveUsers
} from '../src/mock/data/community.mock'

import {
  mockCourses,
  mockCollections,
  mockWrongQuestions,
  mockBadges,
  mockUserBadges
} from '../src/mock/data/learning.mock'

import {
  mockAssessments,
  mockAssessmentResults
} from '../src/mock/data/assessment.mock'

import {
  mockRegisterUser
} from '../src/mock/data/auth.mock'

import {
  mockNotifications,
  mockNotificationPreferences
} from '../src/mock/data/notification.mock'

import {
  mockJobPositions,
  mockSkillTree,
  mockJobMatchResults
} from '../src/mock/data/job.mock'

import {
  mockSystemConfigs,
  mockSystemAnnouncements
} from '../src/mock/data/system.mock'

const outputDir = join(__dirname, '../docs/seed-data')
mkdirSync(outputDir, { recursive: true })

function save(filename: string, data: unknown) {
  const path = join(outputDir, filename)
  writeFileSync(path, JSON.stringify(data, null, 2), 'utf-8')
  console.log(`✅ Exported: ${filename}`)
}

// ---- 按模块导出 ----

// Auth 模块 (仅用户数据，token 不需要)
save('auth/users.json', [mockUser, mockRegisterUser])

// User 模块
save('user/interview_history.json', mockInterviewHistory)
save('user/ability_data.json', mockAbilityData)
save('user/resume_data.json', mockResumeData)
save('user/resume_diagnosis.json', mockResumeDiagnosisResult)

// Interview 模块
save('interview/sessions.json', mockInterviewSessions)
save('interview/reports.json', [mockInterviewReport])
save('interview/game_levels.json', mockGameLevels)
save('interview/game_stats.json', [mockGameStats])
save('interview/game_achievements.json', mockGameAchievements)
save('interview/leaderboard.json', mockLeaderboard)
save('interview/game_interview_data.json', mockGameInterviewData)

// Community 模块
save('community/posts.json', mockPosts)
save('community/comments.json', mockComments)
save('community/hot_topics.json', mockHotTopics)
save('community/active_users.json', mockActiveUsers)

// Learning 模块
save('learning/courses.json', mockCourses)
save('learning/collections.json', mockCollections)
save('learning/wrong_questions.json', mockWrongQuestions)
save('learning/badges.json', mockBadges)
save('learning/user_badges.json', mockUserBadges)

// Assessment 模块
save('assessment/assessments.json', mockAssessments)
save('assessment/results.json', mockAssessmentResults)

// Notification 模块
save('notification/notifications.json', mockNotifications)
save('notification/preferences.json', [mockNotificationPreferences])

// Job 模块
save('job/positions.json', mockJobPositions)
save('job/skill_tree.json', [mockSkillTree])
save('job/match_results.json', mockJobMatchResults)

// System 模块
save('system/configs.json', mockSystemConfigs)
save('system/announcements.json', mockSystemAnnouncements)

console.log('\n🎉 All mock data exported to docs/seed-data/')
```

#### 1.2 运行导出

```bash
npx tsx scripts/export-mock-data.ts
```

产出目录结构：

```
docs/seed-data/
├── auth/
│   └── users.json
├── user/
│   ├── interview_history.json
│   ├── ability_data.json
│   ├── resume_data.json
│   └── resume_diagnosis.json
├── interview/
│   ├── sessions.json
│   ├── reports.json
│   ├── game_levels.json
│   ├── game_stats.json
│   ├── game_achievements.json
│   ├── leaderboard.json
│   └── game_interview_data.json
├── community/
│   ├── posts.json
│   ├── comments.json
│   ├── hot_topics.json
│   └── active_users.json
├── learning/
│   ├── courses.json
│   ├── collections.json
│   ├── wrong_questions.json
│   ├── badges.json
│   └── user_badges.json
├── assessment/
│   ├── assessments.json
│   └── results.json
├── notification/
│   ├── notifications.json
│   └── preferences.json
├── job/
│   ├── positions.json
│   ├── skill_tree.json
│   └── match_results.json
└── system/
    ├── configs.json
    └── announcements.json
```

---

### Phase 2：后端 Seed 脚本（后端团队完成）

**目标：** 在后端仓库中编写 Alembic seed migration，将 JSON 数据写入 PostgreSQL。

**给后端团队的交付物：**
1. `docs/seed-data/` 目录下所有 JSON 文件
2. 本文档（含数据结构说明和依赖关系）
3. OpenAPI 规范（`docs/api/openapi.json`，281KB）

#### 2.1 后端 Seed 脚本模板（供后端参考）

```python
# backend/alembic/versions/xxxx_seed_initial_data.py
"""Seed initial data from frontend mock

Revision ID: xxxx
Revises: 37f0b8c56d5c
Create Date: 2026-06-03
"""

import json
from pathlib import Path
from alembic import op
from sqlalchemy import table, column
from sqlalchemy import String, Integer, Boolean, DateTime, Text, Float, JSON

# revision identifiers
revision = 'xxxx'
down_revision = '37f0b8c56d5c'
branch_labels = None
depends_on = None

SEED_DIR = Path(__file__).parent.parent.parent / 'seed-data'


def load_json(filename: str) -> list | dict:
    """加载 seed JSON 文件"""
    filepath = SEED_DIR / filename
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def upgrade() -> None:
    """插入初始种子数据"""

    # === 1. 用户表 ===
    users = load_json('auth/users.json')
    users_table = table('users',
        column('id', Integer),
        column('username', String),
        column('email', String),
        column('phone', String),
        column('is_active', Boolean),
        column('hashed_password', String),
        # ... 根据实际表结构补充
    )
    for user in users:
        op.execute(
            users_table.insert().values(
                id=user['id'],
                username=user['username'],
                email=user['email'],
                phone=user.get('phone'),
                is_active=user.get('is_active', True),
                hashed_password='seed_placeholder_hash',  # 种子用户需重置密码
            )
        )

    # === 2. 职位表 ===
    positions = load_json('job/positions.json')
    # ... 类似模式

    # === 3. 课程表 ===
    courses = load_json('learning/courses.json')
    # ... 类似模式

    # === 4. 帖子表（依赖用户表） ===
    posts = load_json('community/posts.json')
    # ... 类似模式

    # === 5. 评论表（依赖帖子表和用户表） ===
    comments = load_json('community/comments.json')
    # ... 类似模式

    # ... 其他表按依赖顺序插入


def downgrade() -> None:
    """删除种子数据（按逆序）"""
    op.execute("DELETE FROM comments WHERE id <= 100")
    op.execute("DELETE FROM posts WHERE id <= 100")
    op.execute("DELETE FROM courses WHERE id <= 100")
    op.execute("DELETE FROM positions WHERE id <= 100")
    op.execute("DELETE FROM users WHERE id <= 10")
```

#### 2.2 数据依赖关系（插入顺序）

```
第 1 层（无依赖）：
├── users (用户)
├── system_configs (系统配置)
├── system_announcements (系统公告)
├── badges (徽章定义)
├── job_positions (职位)
├── skill_tree (技能树)
└── courses (课程)

第 2 层（依赖第 1 层）：
├── assessment (测评，无外部依赖)
├── notification_preferences (通知偏好，依赖 users)
├── user_badges (用户徽章，依赖 users + badges)
├── collections (收藏，依赖 users + courses)
└── hot_topics (热门话题)

第 3 层（依赖第 2 层）：
├── posts (帖子，依赖 users)
├── wrong_questions (错题，依赖 users + courses)
├── interview_sessions (面试会话，依赖 users + job_positions)
└── resume_data (简历，依赖 users)

第 4 层（依赖第 3 层）：
├── comments (评论，依赖 posts + users)
├── interview_reports (面试报告，依赖 interview_sessions)
├── game_levels (游戏关卡)
├── game_achievements (游戏成就)
└── notifications (通知，依赖 users)

第 5 层（依赖第 4 层）：
├── assessment_results (测评结果，依赖 assessment)
├── job_match_results (岗位匹配，依赖 job_positions + users)
├── leaderboard (排行榜，依赖 users)
└── interview_history (面试历史，依赖 users + job_positions)
```

---

### Phase 3：前端清理（前端完成）

**目标：** 后端 seed 数据就绪后，移除前端 Mock 降级逻辑，确保所有数据来自 API。

#### 3.1 清理优先级

| 优先级 | 任务 | 涉及文件 |
|--------|------|----------|
| **P0** | 移除 Store 中的 mock fallback | `src/stores/user.ts`, `src/stores/learning.ts` |
| **P0** | 设置 `VITE_USE_MOCK=false` | `.env.development` |
| **P1** | 清理组件内联硬编码数据 | 9 个 View 文件 |
| **P2** | 保留 Mock 基础设施（开发调试用） | `src/mock/` 目录 |
| **P3** | 清理 Mock 数据文件（可选） | `src/mock/data/` |

#### 3.2 Store fallback 清理示例

```typescript
// src/stores/user.ts - 修改前
async fetchInterviewHistory() {
  try {
    const res = await userApi.getInterviewHistory()
    this.interviewHistory = res.data
  } catch {
    // fallback to mock
    const { mockInterviewHistory } = await import('@/mock/data/user.mock')
    this.interviewHistory = mockInterviewHistory
  }
}

// src/stores/user.ts - 修改后
async fetchInterviewHistory() {
  const res = await userApi.getInterviewHistory()
  this.interviewHistory = res.data
}
```

#### 3.3 组件内联数据迁移建议

对于组件中的内联数据，有两种处理方式：

**方式 A：新增后端 API 端点（推荐）**
- `Knowledge.vue` 中的知识库数据 → 新增 `/api/v1/knowledge/*` 端点
- `Growth.vue` 中的成长数据 → 复用或扩展 `/api/v1/learning/*` 端点
- `Home.vue` 中的首页数据 → 新增 `/api/v1/system/home-data` 端点

**方式 B：提取到 Mock 文件 + 后续迁移**
- 先将内联数据提取到 `src/mock/data/` 中
- 再按 Phase 1-2 流程迁移到后端

---

## 四、风险与注意事项

### 4.1 数据 ID 映射

- Mock 中的 `id` 是硬编码的数字（如 `id: 1`），数据库自增 ID 可能冲突
- **建议：** Seed 数据使用高起始值（如 `id >= 10000`），避免与正常数据冲突

### 4.2 用户认证

- Seed 用户的密码需要特殊处理（不能存明文）
- **建议：** Seed 用户使用固定的已知密码哈希，或标记为"需重置密码"

### 4.3 时间戳

- Mock 数据中的时间戳是静态的（如 `created_at: "2024-01-15"`）
- **建议：** Seed 脚本中保留原始时间戳，或统一设置为项目启动时间

### 4.4 关联数据一致性

- 如 `mockPosts` 中的 `author_id` 必须对应 `users` 表中的有效 ID
- **建议：** 严格按照依赖关系顺序插入

### 4.5 组件内联数据 vs 正式 Mock

- 组件内联数据（`src/views/` 中的）**尚未纳入**标准 Mock 体系
- 这些数据的结构可能与后端 API 返回格式不一致
- **建议：** 先将内联数据提取到 `src/mock/data/`，统一类型定义后再迁移

---

## 五、执行时间线

| 阶段 | 负责方 | 预计工时 | 产出 | 实际状态 |
|------|--------|----------|------|----------|
| Phase 1: 数据提取 | 前端 | 0.5 天 | `docs/seed-data/*.json` | ✅ 已完成 (2026-06-03) |
| Phase 2: Seed 脚本 | 后端 | 1-2 天 | Alembic migration | ⏳ 待执行 |
| Phase 3: 前端清理 | 前端 | 1 天 | 移除 mock fallback | ⏳ 待执行 |
| 测试验证 | 前后端 | 1 天 | 确认数据一致性 | ⏳ 待执行 |
| **总计** | | **3-4.5 天** | | |

---

## 六、验证清单

- [x] 所有 `src/mock/data/*.mock.ts` 中的数据已导出为 JSON ✅ (30 个文件，98 条记录)
- [ ] JSON 文件结构与 OpenAPI 规范中的 schema 一致
- [ ] 后端 seed 脚本执行成功（`alembic upgrade head`）
- [ ] 前端 `VITE_USE_MOCK=false` 后所有页面数据正常显示
- [ ] Store 中的 mock fallback 已移除
- [ ] API 返回的数据结构与前端类型定义匹配
- [ ] Seed 数据的 ID 不与后续正常数据冲突
- [ ] 所有关联数据（外键）引用正确

---

## 附录 A：Mock 数据与 API 端点映射表

| Mock 文件 | 导出变量 | API 端点 | HTTP 方法 |
|-----------|----------|----------|-----------|
| user.mock.ts | mockUser | `/api/v1/user/profile` | GET |
| user.mock.ts | mockInterviewHistory | `/api/v1/interview/history` | GET |
| user.mock.ts | mockAbilityData | `/api/v1/user/ability` | GET |
| user.mock.ts | mockResumeData | `/api/v1/user/resume` | GET |
| interview.mock.ts | mockInterviewSessions | `/api/v1/interview/sessions` | GET |
| interview.mock.ts | mockGameLevels | `/api/v1/interview/game/levels` | GET |
| interview.mock.ts | mockGameAchievements | `/api/v1/interview/game/achievements` | GET |
| interview.mock.ts | mockLeaderboard | `/api/v1/interview/game/leaderboard` | GET |
| community.mock.ts | mockPosts | `/api/v1/community/posts` | GET |
| community.mock.ts | mockComments | `/api/v1/community/posts/{id}/comments` | GET |
| learning.mock.ts | mockCourses | `/api/v1/learning/courses` | GET |
| learning.mock.ts | mockCollections | `/api/v1/learning/collections` | GET |
| learning.mock.ts | mockWrongQuestions | `/api/v1/learning/wrong-questions` | GET |
| learning.mock.ts | mockBadges | `/api/v1/learning/badges` | GET |
| assessment.mock.ts | mockAssessments | `/api/v1/assessments` | GET |
| assessment.mock.ts | mockAssessmentResults | `/api/v1/assessments/{id}/results` | GET |
| notification.mock.ts | mockNotifications | `/api/v1/notifications` | GET |
| job.mock.ts | mockJobPositions | `/api/v1/jobs` | GET |
| job.mock.ts | mockSkillTree | `/api/v1/jobs/skill-tree` | GET |
| system.mock.ts | mockSystemConfigs | `/api/v1/system/configs` | GET |
| system.mock.ts | mockSystemAnnouncements | `/api/v1/system/announcements` | GET |

## 附录 B：不入库的数据

以下 Mock 数据是**运行时生成**或**认证相关**的，不需要写入数据库：

| 数据 | 原因 |
|------|------|
| `mockToken` | JWT token 由后端动态生成 |
| `mockLoginResponse` | 包含 token，运行时组合 |
| `mockSystemHealth` | 运行时状态，查询即得 |
| `mockNotificationPreferences` | 用户个人设置，默认值由后端提供 |
| `mockRegisterUser` | 注册模板，实际用户通过注册流程创建 |
| `SSE_CHAT_RESPONSES` | AI 面试对话，由 AI 服务动态生成 |
