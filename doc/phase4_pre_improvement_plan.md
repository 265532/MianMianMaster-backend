# 阶段四前基础非LLM模块改进与建设规划

## 1. 概述
根据《AI模拟面试与能力提升软件需求分析》及项目的开发阶段规划，当前项目已完成阶段一至阶段三的核心基建（用户体系、测评体系、学习系统）。为保障阶段四（AI面试与调度核心）的顺利开展，需要提前完善相关的基础非LLM模块，并预留清晰的接口供后续LLM接入。

本文档针对“面试复盘社区”、“游戏化机制闭环”、“文档与数据库一致性”及“性能、安全与合规性”四大核心模块，分析了现状并制定了改进与建设规划。

---

## 2. 核心模块建设规划

### 2.1 面试复盘社区 (Community)
**【现状分析】**：当前代码库中尚未实现 `Post`、`Comment`、`UserFollow` 等社区核心模型，原定于阶段五开发。根据最新规划，需提前至阶段四前完成基础数据结构与 CRUD，以便阶段四的 LLM 模块直接与之交互。

**【改进计划】**：
- **模型设计**：
  - `Post`：帖子/文章表，包含标题、内容、分类（面试复盘、真题分享、经验交流）、状态。
  - `Comment`：评论表，支持帖子下的层级评论互动。
  - `PostLike` & `UserFollow`：点赞与用户关注关联表。
- **接口开发**：
  - 开发社区信息流（Feed）分页查询、搜索接口。
  - 实现发帖、评论、点赞、关注等基础业务 API。
- **LLM 预留接口 (扩展性)**：
  - 预留 `ai_analysis_status` 和 `ai_review_content` 字段。
  - 预留 API 接口：`POST /api/v1/community/posts/{post_id}/ai-review`，内部暂留空或通过异步任务放入消息队列，为后续 LLM 自动点评帖子做准备。

### 2.2 游戏化机制闭环 (Gamification Loop)
**【现状分析】**：在阶段三已实现基础的 `Badge` (徽章) 和 `UserBadge` 模型，并提供了手动颁发接口，但缺乏自动触发闭环和体系化的积分/等级系统，导致“游戏化”未形成完整闭环。

**【改进计划】**：
- **完善积分与等级模型**：
  - 在 `UserProfile` 中新增 `experience_points` (经验值) 和 `level` (等级) 字段。
  - 增加 `UserDailyTask` (日常任务记录) 模型，用于日常活跃度驱动。
- **建立自动触发闭环 (Service Hook)**：
  - 学习闭环：在 `learning_service.py` 中，当用户学习进度达到 100% 时，系统自动触发 `award_badge`。
  - 测评闭环：在提交测评并计算得分后，若达到设定阈值（如 > 80分），自动发放能力证明徽章。
- **LLM 预留接口 (扩展性)**：
  - 为未来的“游戏通关式面试”预留模型配置。在 `Badge` 或关卡配置中增加 `ai_prompt_override` 字段，用于后续接入特定人设的 AI 面试官。

### 2.3 文档与数据库一致性 (Consistency)
**【现状分析】**：经比对 `init.sql`、Alembic 迁移脚本与 `src/models` 发现，存在部分字段命名差异（如 `blockchain_hash` 与 `tx_hash`）、部分表字段遗漏以及文档 `ai_coding_plan.md` 进度滞后等问题。

**【改进计划】**：
- **Schema 严格对齐**：
  - 以 `src/models` 下的 SQLAlchemy 2.0 模型为基准（SSOT），审计并修复 `doc/database/init.sql` 中的遗漏字段（如 `permissions` 表的 `updated_at`、`resource` 等差异）。
  - 核对所有外键的 `ondelete="CASCADE"` 约束，防止脏数据残留。
- **文档状态刷新**：
  - 更新 `doc/ai_coding_plan.md`，将阶段五的社区模块标记为“提前至阶段四前”并更新 Todo。
  - 完善各个模块的 `handover.md`（如 `doc/learning/handover.md`），清理不再适用的过时记录。

### 2.4 性能、安全与合规性 (Performance, Security & Compliance)
**【现状分析】**：系统目前采用 bcrypt 密码哈希和 JWT 机制，且实现了基于 Redis 的 RBAC 缓存。但在 API 接口防刷、响应数据脱敏及 ORM 查询性能（N+1 问题）上仍有欠缺。

**【改进计划】**：
- **性能优化 (N+1 排查)**：
  - 全面排查 `src/services` 中的查询逻辑，特别是获取用户列表、角色列表时，确保使用 `selectinload` 预加载 `roles` 和 `permissions`。
- **安全加固 (限流防刷)**：
  - 引入 `slowapi` 库，为核心敏感接口（`/api/v1/auth/register`、`/api/v1/auth/login`、`/api/v1/auth/send-sms`）增加 IP 与用户级别的频次限制。
- **数据脱敏合规**：
  - 检查 Pydantic 响应模型 (`schemas/user.py`)，确保返回数据中彻底屏蔽密码哈希，并对手机号（`phone`）等敏感信息在普通场景下进行打码脱敏（如 `138****1234`）。
  - 在全局日志配置中，加入敏感词过滤，防止密码和 Token 被打印至控制台或日志文件。

---

## 3. 后续行动建议
建议在接下来的 AI Coding 对话中，按照以下顺序依次拆解执行：
1. **执行一致性修复与安全加固**：修正模型与数据库脚本差异，引入限流与脱敏。
2. **闭环游戏化系统**：补全经验值字段及各种自动触发的 Service Hook。
3. **建设社区基础模块**：完成 `Post` 等相关表及 CRUD 接口。
4. **验证与测试**：通过 Pytest 跑通上述所有非 LLM 链路，确保无误后进入阶段四。
