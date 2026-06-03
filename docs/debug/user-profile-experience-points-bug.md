# Bug Report: 注册接口 500 错误 - user_profiles.experience_points 字段不存在

## 错误现象

`POST /api/v1/auth/register` 注册用户时返回 `500 Internal Server Error`，报错：

```
ProgrammingError: (psycopg2.errors.UndefinedColumn) 错误: 字段 user_profiles.experience_points 不存在
```

## 根本原因

**数据库表结构与 SQLAlchemy ORM 模型不一致。**

- SQLAlchemy 模型 `UserProfile`（[src/models/user.py:29-30](src/models/user.py#L29-L30)）定义了 `experience_points` 和 `level` 两个字段
- 数据库 `user_profiles` 表中**不存在**这两个列
- 唯一的 Alembic 迁移文件 `37f0b8c56d5c` 中没有添加这两个列的操作

## 错误链路

1. 用户注册成功，数据库写入 User 记录（返回 200）
2. FastAPI 序列化响应时，Pydantic `User` schema 的 `profile` 字段触发 SQLAlchemy 懒加载
3. SQLAlchemy 生成 SQL 查询 `SELECT ... experience_points, level ... FROM user_profiles`
4. PostgreSQL 报错 `UndefinedColumn`：`experience_points` 列不存在
5. 错误向上抛出，FastAPI 抛出 `ResponseValidationError` → 500

## 涉及文件

| 文件 | 说明 |
|------|------|
| [src/models/user.py:29-30](src/models/user.py#L29-L30) | ORM 模型定义了 `experience_points`、`level` |
| [docs/database/init.sql:91-92](docs/database/init.sql#L91-L92) | init.sql 包含这两个字段（未执行到实际数据库） |
| [alembic/versions/37f0b8c56d5c](alembic/versions/37f0b8c56d5c_add_learning_phase_3_models.py) | 唯一的迁移文件，缺少这两个字段的 add_column 操作 |

## 修复方案

### 方案一：创建 Alembic 迁移（推荐）

```bash
alembic revision --autogenerate -m "add_experience_points_and_level_to_user_profiles"
alembic upgrade head
```

### 方案二：直接执行 SQL（快速修复）

```sql
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS experience_points INTEGER DEFAULT 0;
ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS level INTEGER DEFAULT 1;
```

### 修复后验证

重启服务后再次调用 `POST /api/v1/auth/register`，应返回正常 JSON 响应，不再报 500 错误。