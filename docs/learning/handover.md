# Learning & Practice 模块交接文档

## 1. 当前已实现的核心功能清单

本模块主要负责“阶段三：学习与题库系统”的实现，涵盖了课程资源、题库练习和徽章系统三个核心部分。

### 1.1 课程与资源库 (Course & Materials)
- **模型设计**：
  - `Course` (课程基础信息)
  - `CourseMaterial` (课程资料，支持 video, pdf, article，关联知识图谱节点)
  - `UserLearningProgress` (记录用户在各个资料上的学习进度及完成状态)
- **API 接口**：
  - `POST /api/v1/learning/courses` - 创建课程
  - `GET /api/v1/learning/courses` - 分页获取课程列表
  - `POST /api/v1/learning/materials` - 为课程添加资料
  - `POST /api/v1/learning/progress/update` - 更新用户学习进度
  - `GET /api/v1/learning/progress/{course_id}` - 获取用户在某课程的详细进度

### 1.2 专属题库与练习 (Question Bank)
- **模型设计**：
  - 调整 `Question` 模型，解耦与 `Assessment` 的强制绑定关系，使其可用于日常题库练习。
  - `UserQuestionCollection` (用户题目收藏夹，支持个人笔记)
  - `UserWrongQuestion` (用户错题本，记录错误答案及答错次数)
- **API 接口**：
  - `POST /api/v1/learning/collections` - 收藏题目
  - `GET /api/v1/learning/collections` - 获取收藏列表
  - `POST /api/v1/learning/wrong-questions` - 记录错题
  - `GET /api/v1/learning/wrong-questions` - 获取错题列表
  - `POST /api/v1/learning/wrong-questions/{question_id}/master` - 标记错题为已掌握

### 1.3 游戏化与徽章系统 (Gamification)
- **模型设计**：
  - `Badge` (徽章定义，包含触发条件 `condition_type` 和 `condition_value`，以及为 LLM 预留的 `ai_prompt_override`)
  - `UserBadge` (用户徽章关联，预留 `tx_hash` 供后续区块链存证扩展)
  - `UserDailyTask` (用户日常任务表，位于 `gamification.py`)
  - `UserProfile` (新增 `experience_points` 经验值和 `level` 等级字段)
- **API 接口**：
  - `POST /api/v1/learning/badges` - 创建徽章定义
  - `GET /api/v1/learning/badges` - 获取徽章列表
  - `POST /api/v1/learning/badges/award/{badge_id}` - 为用户颁发徽章
  - `GET /api/v1/learning/my-badges` - 获取当前用户的徽章
- **Service Hook**：
  - 学习进度 100% 完成时，自动颁发 `course_completed` 类型的徽章，并增加经验值。
  - 测评得分 > 80 分时，自动颁发 `score_reached` 类型的徽章，并增加经验值。

---

## 2. 未完成的 Todo 事项

- 刷题与随机抽题的复合业务逻辑（如根据岗位/知识图谱动态生成练习卷）目前尚未在 `learning` API 中完全实现，未来可结合 `assessment` 模块进行完善。
- 课程与资料的上传暂未对接 OSS/MinIO 存储，目前 URL 为字符串直存，需要后续在后台管理中实现上传逻辑。
- 区块链上链存证逻辑目前仅在 `UserBadge` 模型中预留了 `tx_hash` 字段，需在后续扩展。

---

## 3. 关键技术决策说明

- **模型存放位置**：所有新增的学习、题库、徽章模型统一放置在 `src/models/learning.py` 中，保持模块的高内聚。
- **题目复用**：放弃创建独立的 `PracticeQuestion` 表，而是修改现有的 `src/models/assessment.py` 中的 `Question` 表，将其 `assessment_id` 外键设置为 `nullable=True`，使得题目可以独立于试卷存在，实现测评题与练习题的复用。
- **异常处理**：在 Service 层统一使用了 `src.core.exceptions.BusinessException` 替代 `HTTPException`，以符合项目统一 JSON 响应格式规约。
- **数据库迁移**：历史版本中遗留的 `practice_questions` 等表通过级联删除并在 Alembic 中手动调整外键依赖顺序，确保了数据迁移的顺利进行。

---

## 4. 下一步开发建议

- 推荐进入 **阶段四：AI 面试与调度核心 (AI Interview Agent)** 的开发。
- 在后续开发 AI 智能追问或生成评估报告时，可以读取本模块中的 `UserWrongQuestion` 数据，以辅助大模型判断候选人的真实薄弱环节。
