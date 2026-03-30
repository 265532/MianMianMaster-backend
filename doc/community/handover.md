# Community (面试复盘社群) 模块交接文档

## 1. 当前已实现的核心功能清单

本模块原定于阶段五，为配合阶段四 AI 核心模块的 LLM 接入需求，已提前至阶段四前完成基础建设。主要负责“面试复盘社群”的核心数据结构及基础信息流。

### 1.1 面试复盘社群 (Community)
- **模型设计**：
  - `Post` (帖子/文章表，包含标题、内容、分类、状态，并为 LLM 预留了 `ai_analysis_status` 和 `ai_review_content` 字段)
  - `Comment` (评论表，支持层级评论互动)
  - `PostLike` (点赞关联表)
  - `UserFollow` (用户关注关联表)
- **API 接口**：
  - `POST /api/v1/community/posts` - 创建帖子
  - `GET /api/v1/community/posts/feed` - 获取社区信息流（支持分页、搜索）
  - `GET /api/v1/community/posts/{post_id}` - 获取帖子详情
  - `POST /api/v1/community/posts/{post_id}/comments` - 创建评论
  - `POST /api/v1/community/posts/{post_id}/like` - 帖子点赞/取消点赞
  - `POST /api/v1/community/users/{user_id}/follow` - 关注/取消关注用户
  - `POST /api/v1/community/posts/{post_id}/ai-review` - 触发 AI 自动点评（目前仅更改状态，等待后续 LLM 接入）

---

## 2. 未完成的 Todo 事项

- LLM 自动点评帖子功能：`ai-review` 接口目前只是将状态变更为 `processing`，实际需要在阶段四/五引入消息队列和 LLM 服务来进行异步点评并回写 `ai_review_content`。
- 将个人的面试报告/错题一键分享为帖子的快捷接口尚未开发，目前只有基础发帖接口。
- 评论的点赞和分页查询尚未实现。
- 热榜或推荐算法（基于点赞、评论数）尚未实现，目前 `feed` 接口仅通过创建时间倒序。

---

## 3. 关键技术决策说明

- **模型独立性**：为了后续扩展，所有社区相关的模型统一存放在 `src/models/community.py`。
- **预留 LLM 字段**：在 `Post` 中增加了 `ai_analysis_status` 和 `ai_review_content`，目的是为了在阶段四开发中，LLM Agent 可以直接针对用户的复盘帖子进行评估和建议。

---

## 4. 下一步开发建议

- 随着本模块和 Gamification 模块的完善，当前阶段（阶段四前非 LLM 模块基建）已结束。
- 下一步应直接进入 **阶段四：AI 面试与调度核心 (AI Interview Agent)**，并可利用本模块中预留的 `ai-review` 接口进行 LLM 整合测试。
