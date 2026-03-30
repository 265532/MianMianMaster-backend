# 修复 FastAPI limiter 导致的循环依赖问题 (Circular Import)

## 问题描述
运行 `python -m src.main` 启动应用时，抛出 `ImportError: cannot import name 'api_router' from partially initialized module 'src.api.router' (most likely due to a circular import)` 异常。

触发原因：
- `src.main` 中定义并初始化了 `limiter = Limiter(...)`，并向应用挂载路由 `from src.api.router import api_router`。
- `src.api.router` 中引入了 `src.api.v1.auth` 模块。
- `src.api.v1.auth` 路由中因为使用了 `@limiter.limit` 装饰器，向 `src.main` 导入了 `limiter`。
这就形成了 `src.main` -> `src.api.router` -> `src.api.v1.auth` -> `src.main` 的循环依赖。

## 解决方案
**解耦依赖，将 `limiter` 的初始化逻辑移至独立的模块**。
1. 在核心配置目录下新建独立文件 `src/core/limiter.py`，专门负责实例化 `Limiter`。
2. 调整 `src.main` 中的导入逻辑，由之前自行实例化改为 `from src.core.limiter import limiter`。
3. 调整 `src.api.v1.auth` 中的导入路径，将 `from src.main import limiter` 更改为 `from src.core.limiter import limiter`。

## 最佳实践与踩坑记录
1. **不要在应用入口文件（`main.py`）中定义被其他子模块依赖的对象**：
   像 FastAPI 的全局异常处理器、请求频率限制器（Limiter）、数据库引擎（Engine）等对象，应该尽可能放置于独立的 `src/core/` 或者 `src/db/` 目录下。
2. **避免由下往上的反向依赖**：
   路由层（Router）和业务层（Service）应尽量避免从主应用入口（`main.py`）导入资源，否则非常容易在项目扩展时引发循环引用。
