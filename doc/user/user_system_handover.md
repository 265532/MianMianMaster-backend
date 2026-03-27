# 基础用户系统深化与个人中心交接文档

## 1. 概述
在完成基础用户系统（RBAC、JWT、短信登录等）之后，根据项目需求分析文档的“阶段一”目标，对用户体系进行了进一步深化，主要新增了“个人中心扩展信息（UserProfile）”与“消息通知系统（Notification）”，以及相关账号安全设置。

## 2. 数据库更新设计
更新了数据库初始化脚本 `doc/database/init.sql`，主要新增两张核心表：
- `user_profiles`: 存储用户扩展信息（头像 `avatar_url`、学历 `education`、目标岗位 `target_position`、工作年限 `work_years`），与 `users` 表形成 1-to-1 的关联（通过 `user_id` 唯一约束及级联删除）。
- `notifications`: 消息通知表，用于存储系统下发给用户的通知（标题、内容、类型 `type`、已读状态 `is_read`），通过 `user_id` 与用户表关联。

## 3. 核心功能实现
### 3.1 用户扩展信息 (User Profile)
- **API 路由**: 集中于 `src/api/v1/user.py`，基础前缀 `/api/v1/user`。
- **获取信息**: `GET /profile`。当用户首次请求获取时，若不存在 Profile，系统会在底层 Service 自动为其初始化一条空的 Profile 记录并返回，避免前端取不到数据。
- **更新信息**: `PUT /profile`。支持局部更新扩展信息，采用 Pydantic 的 `exclude_unset=True`。

### 3.2 账号安全设置 (Account Security)
- **API 路由**: 同样位于 `src/api/v1/user.py`。
- **修改密码**: `POST /security/change-password`。要求校验旧密码，新密码强制经过相同的强度校验规则，并使用 `bcrypt` 重新 Hash 存储。
- **修改手机号**: `POST /security/change-phone`。校验请求中提供的验证码（来自 `sms_verifications` 表），校验通过且手机号未被其他用户占用时进行更换。

### 3.3 消息通知系统 (Notification)
- **API 路由**: 位于 `src/api/v1/notification.py`，基础前缀 `/api/v1/notifications`。
- **功能清单**:
  - `GET /`：支持分页获取当前用户的消息列表，按时间倒序排列。
  - `GET /unread-count`：获取未读消息总数，便于前端红点展示。
  - `PUT /{id}/read`：将单条消息标记为已读。
  - `PUT /read-all`：将该用户所有未读消息一键标记为已读。
  - `POST /`：创建通知的内部接口（当前为测试/内部调用预留）。

## 4. 技术与规范说明
- 遵循 `Router -> Service -> DB (Model)` 的三层架构，新增了 `src/services/user_service.py` 和 `src/services/notification_service.py` 处理业务逻辑。
- Schema 层严格使用 Pydantic v2 规范，并通过 `ResponseModel` 统一包装返回。
- 增加了对应的 Pytest 单元测试，涵盖了 Profile 的自动创建、更新，以及 Notification 完整生命周期的断言，所有测试用例已全部通过。

## 5. 后续待优化项
- `UserProfile` 的头像上传暂为文本 URL，需在后续阶段接入对象存储（如 OSS/S3）的上传功能。
- 消息通知类型当前支持字符串，后期可考虑使用 `Enum` 并引入 Websocket 以实现服务端主动推送提醒。
