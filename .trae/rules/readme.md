# MianMianMaster Backend - 内部文档导航

欢迎来到 MianMianMaster 后端项目的内部文档库。这里的文档主要用于团队协作、规范对齐以及为 AI 辅助编程提供上下文。

## 核心规约与规划 (Core Specifications & Plans)

> **最高准则**：当代码与任何外部认知发生冲突时，请以以下规约和 `src/` 目录下的实际代码为准。

- 📜 **[AI 开发规约合订版](./ai-development-specification.md)** 
  项目的架构约束、技术栈选型（FastAPI + SQLAlchemy 同步风格）、包管理、代码风格等核心规范的统一集合。
- 🎯 **[AI Coding 开发规划](/docs/ai_coding_plan.md)**
  基于产品需求分析文档拆解的开发迭代计划，AI 每次开发新功能前需查阅此文档。
- 📊 **[软件需求分析](/docs/AI模拟面试与能力提升软件需求分析.md)**
  产品的原始业务需求和功能全景图。

## 模块交接文档 (Handovers)

为保证业务开发的连续性，每次完成特定模块开发后需生成的上下文交接文档，存放在 `docs/模块名/` 目录下，文件名格式为 `模块名_handover.md`，例如：

- 👤 **[用户系统模块交接](/docs/user/user_system_handover.md)**

## 经验与排坑记录 (Knowledge Base)

记录开发过程中遇到的关键问题及解决方案，存放在 `docs/debug/` 目录下，文件名格式为 `问题描述.md`，例如：

- 🐛 **[Bcrypt 与 Passlib 注册修复记录](/docs/debug/passlib_bcrypt_and_register_fix.md)**

## 数据库资料 (Database)

- 💾 **[初始化 SQL 脚本](/docs/database/init.sql)**

---

*注：IDE 的 AI 提示词配置文件存放在项目根目录的 `.trae/rules/` 文件夹中，由开发工具自动读取。*
