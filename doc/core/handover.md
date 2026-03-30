# Core 模块交接文档

## 当前进度
- 核心配置文件 `config.py` 和异常处理 `exceptions.py`。
- 请求速率限制器 `limiter` 的独立化：为解决 FastAPI 路由和主应用之间的循环依赖问题，将 `slowapi.Limiter` 的实例化提取到了独立的 `src/core/limiter.py` 文件中。

## 关键技术决策
- **Limiter 解耦设计**：为了避免由于 `@limiter.limit` 装饰器从 `src.main` 中反向导入导致的循环引用问题（如 `auth.py` 与 `main.py` 循环），采取将所有请求限制、全局拦截等核心对象抽离至 `core/` 下的独立文件中进行管理。
- **配置与安全**：保留了基于 `slowapi` 和 `get_remote_address` 的 IP 限流功能。

## 待办事项 (Todo)
- [ ] 随着业务增长，考虑将 Limiter 接入 Redis 以支持分布式速率限制。
- [ ] 根据未来需求进一步拆分异常处理、依赖注入等核心逻辑。

## 建议上下文
- 下一位接手的 AI 助手在给路由层添加 `@limiter.limit` 装饰器时，请统一使用 `from src.core.limiter import limiter`，严禁从 `src.main` 中导入。
