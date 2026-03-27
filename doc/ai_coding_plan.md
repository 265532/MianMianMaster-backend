# AI Coding 开发规划文档 (基于需求分析)

本文档基于 `AI模拟面试与能力提升软件需求分析.md`，将整个庞大的需求拆解为**可落地的 AI Coding 迭代计划**。每次与 AI 助手的新对话，应选取以下的一个或多个子任务作为目标，并在完成后更新对应的 `handover.md` 交接文档。

---

## 阶段一：核心基建与用户体系深化（已完成）

目前项目已经搭建了基础的 FastAPI 框架、RBAC 权限、JWT 登录和短信登录骨架。接下来需要根据需求分析文档，完善用户中心的基础数据结构。

### 1. 完善用户信息与扩展表 (User Profile)
- **目标**：实现需求文档中“个人中心”的“头像和基本信息”及“账号安全”功能。
- **任务拆解**：
  - [x] 在 `User` 模型中增加或扩展关联表：`avatar_url`, `education`, `target_position`, `work_years`。
  - [x] 创建 `UserProfile` 相关的 schemas, service, 和 router。
  - [x] 实现用户信息的查询与修改接口。
  - [x] 实现手机绑定/修改、密码修改等账号安全接口。
- **文档输出**：`doc/user/user_system_handover.md`（更新）

### 2. 消息通知系统 (Notification)
- **目标**：实现需求文档中“设置 -> 消息通知”。
- **任务拆解**：
  - [x] 设计 `Notification` 模型（类型：面试结果、学习提醒、系统公告）。
  - [x] 实现消息的创建、未读数统计、标记已读接口。

---

## 阶段二：知识图谱与测评体系（已完成）

此阶段为项目的核心特色，涉及岗位、技能与用户的匹配。

### 1. 岗位与技能树管理 (Skill Tree & Job Position)
- **目标**：实现后台的“题库与流程管理”和学生端的“技能树可视化”。
- **任务拆解**：
  - [x] 重构或扩展现有的 `KnowledgeGraph` 模型，使其支持层级结构（技能树）。
  - [x] 设计 `JobPosition`（岗位）模型，并将岗位与核心技能节点（KnowledgeGraph）进行多对多关联。
  - [x] 提供接口：根据岗位查询完整的技能树。

### 2. 测评系统 (Assessment System)
- **目标**：实现“岗职双维测评”和“岗位适配度模型”。
- **任务拆解**：
  - [x] 设计 `Assessment`（测评试卷）和 `Question`（题目）模型。
  - [x] 设计 `UserAssessmentRecord`（用户测评记录）和 `UserSkillMastery`（用户技能掌握度）模型。
  - [x] 开发测评提交接口：接收用户的答卷，计算各维度得分。
  - [x] 开发岗位匹配度计算逻辑：根据用户的 `UserSkillMastery` 和目标 `JobPosition` 的技能要求，计算匹配百分比。
- **文档输出**：`doc/assessment/assessment_handover.md`（新建）

---

## 阶段三：学习与题库系统 (Learning & Practice)（已完成）

### 1. 课程与资源库 (Learning Resources)
- **目标**：实现后台“资源库管理”及学生端“学习培养方案”。
- **任务拆解**：
  - [x] 设计 `Course` 和 `CourseMaterial` 模型，并关联到具体的知识图谱节点。
  - [x] 设计 `UserLearningProgress` 记录用户的学习进度。
  - [x] 开发后台上传、管理课程资料的接口。

### 2. 专属题库与练习 (Question Bank)
- **目标**：实现“岗位化专属题库”和“我的错题/收藏题库”。
- **任务拆解**：
  - [x] 设计练习题库模型（支持单选、多选、编程题等类型）。
  - [x] 设计 `UserQuestionCollection`（收藏夹）和 `UserWrongQuestion`（错题本）。
  - [x] 开发刷题接口、随机抽题接口及错题/收藏的增删改查。

### 3. 游戏化与徽章系统 (Gamification)
- **目标**：实现“游戏化学习”及“能力认证”。
- **任务拆解**：
  - [x] 设计 `Badge`（徽章）和 `UserBadge`（用户徽章关联）模型。
  - [x] 开发发放徽章的业务逻辑（在完成特定学习任务或关卡后触发）。
  - [x] （可选）预留区块链上链存证的扩展接口字段。

---

## 阶段四：AI 面试与调度核心 (AI Interview Agent)

### 1. 面试会话管理深化
- **目标**：完善 `InterviewSession` 和 `AgentState`，支持多角色和多模态配置。
- **任务拆解**：
  - [ ] 扩展 `InterviewConfig` 支持面试官性格（压力/温和/引导）和类型（技术/HR）配置。
  - [ ] 完善面试会话（Session）的生命周期管理（创建、进行中、完成、异常）。

### 2. AI 面试官集成 (LLM Integration)
- **目标**：实现“多角色AI面试官”与“智能追问”。
- **任务拆解**：
  - [ ] 封装 LLM 服务层（如对接 OpenAI/DeepSeek API）。
  - [ ] 开发本地 RAG 检索逻辑，结合用户的简历和知识库生成追问 Prompt。
  - [ ] 实现流式对话接口（WebSocket 或 Server-Sent Events），支持前端的多模态（语音/文字）交互。

### 3. 多维度 AI 分析报告生成
- **目标**：面试结束后的自动分析与打分。
- **任务拆解**：
  - [ ] 设计 `InterviewReport` 模型，存储内容分析、表达分析等结构化 JSON 数据。
  - [ ] 编写异步任务（Celery 或后台任务），在面试会话结束后，调用 LLM 对对话记录进行全局分析，生成报告并判定是否发放 Offer 认证。

---

## 阶段五：社区与社交互动 (Community)

### 1. 面试复盘社群
- **目标**：实现“面试复盘社群”功能。
- **任务拆解**：
  - [ ] 设计 `Post`（帖子/文章）、`Comment`（评论）模型。
  - [ ] 支持将个人的面试报告/错题一键分享为匿名或实名帖子。
  - [ ] 设计 `UserFollow`（用户关注）和 `PostLike`（点赞）模型。
  - [ ] 开发社区流（Feed）接口及搜索接口。

---

## AI Coding 规范提醒
- 每次开始新的功能开发前，请 AI 查阅本规划文档以明确当前所处阶段。
- 开发过程中严格遵守 `doc/ai-development-specification.md`（如 `Router -> Service -> DB` 分层）。
- 开发完成后，**务必**在对应的 `doc/[module_name]/handover.md` 中更新进度，并将本规划中对应的任务标记为完成（`[x]`）。
