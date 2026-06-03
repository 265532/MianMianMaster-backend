# MianMianMaster Backend - 内部文档导航

欢迎来到 MianMianMaster 后端项目的内部文档库。这里的文档主要用于团队协作、规范对齐以及为 AI 辅助编程提供上下文。

## 核心规约与规划 (Core Specifications & Plans)

> **最高准则**：当代码与任何外部认知发生冲突时，请以以下规约和 `src/` 目录下的实际代码为准。

- 📜 **[AI 开发规约合订版](./ai-development-specification.md)** 
  项目的架构约束、技术栈选型（FastAPI + SQLAlchemy 同步风格）、包管理、代码风格等核心规范的统一集合。
- 🎯 **[AI Coding 开发规划](./ai_coding_plan.md)**
  基于产品需求分析文档拆解的开发迭代计划，AI 每次开发新功能前需查阅此文档。
- 📊 **[软件需求分析](./AI模拟面试与能力提升软件需求分析.md)**
  产品的原始业务需求和功能全景图。

## 审查与路线图 (Audit & Roadmap)

项目阶段性审查成果和后续开发规划：

- 🔍 **[系统性全面审查报告 (2026-05-09)](./debug/systematic-audit-report-2026-05-09.md)**
  代码质量、架构设计、功能完整性、安全性、性能表现、兼容性及文档完备性的综合审查结果。
- 🗺️ **[下一步开发计划与路线图 (Q2-Q3)](./development-roadmap-2026-Q2-Q3.md)**
  基于审查结果制定的结构化开发计划，含优先级任务列表、资源分配、时间节点与里程碑。

## 模块交接文档 (Handovers)

为保证业务开发的连续性，每次完成特定模块开发后需生成的上下文交接文档：

- 👤 **[用户系统模块交接](./user/user_system_handover.md)**
- 📝 **[测评系统模块交接](./assessment/assessment_handover.md)**
- 👥 **[社区系统模块交接](./community/handover.md)**
- 📚 **[学习系统模块交接](./learning/handover.md)**
- ⚙️ **[核心系统模块交接](./core/handover.md)**

## 经验与排坑记录 (Knowledge Base)

记录开发过程中遇到的关键问题及解决方案：

- 🐛 **[Bcrypt 与 Passlib 注册修复记录](./debug/passlib_bcrypt_and_register_fix.md)**
- 🔁 **[循环导入与限流器问题记录](./debug/circular_import_limiter.md)**

## 数据库资料 (Database)

- 💾 **[初始化 SQL 脚本](./database/init.sql)**

---
*注：IDE 的 AI 提示词配置文件存放在项目根目录的 `.trae/rules/` 文件夹中，由开发工具自动读取。*
*文档最后更新: 2026-05-09*
