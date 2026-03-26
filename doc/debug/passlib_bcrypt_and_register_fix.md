# 记录：Passlib Bcrypt 兼容性问题与注册接口修复

## 背景

前端在请求 `/api/v1/auth/register` 接口进行用户注册时，遭遇了 `500 Internal server error` 报错。传入的注册数据包含 `username`、`email`、`phone`、`password` 以及 `role_ids` 等完整字段。

## 异常排查

1. **Passlib 版本不兼容报错**
   通过捕获服务端的错误日志发现，在执行密码哈希加密（`security.get_password_hash`）时抛出了底层异常：
   ```python
   ValueError: password cannot be longer than 72 bytes, truncate manually if necessary
   ```
   **原因**：项目中使用的 `passlib` 库与当前高版本的 `bcrypt` 存在已知的 "Bcrypt Wrap Bug" 检测兼容性问题。`passlib` 在加载 `bcrypt` 后端时，由于无法正确读取现代 `bcrypt` 的版本号，会触发一个错误的 bug 检测逻辑，从而导致在任何长度的密码加密时都抛出 72 字节超长的错误。

2. **业务逻辑缺失**
   在排查业务代码 `src/api/v1/auth.py` 时发现：
   - 模型构建时，未将前端传入的 `phone`、`is_active` 以及 `role_ids` 字段进行持久化处理。
   - 接口仅校验了 `username` 的唯一性，若前端传入了数据库中已存在的 `email` 或 `phone`，SQLAlchemy 在提交事务时会抛出未被捕获的 `IntegrityError`（违反唯一约束），从而引发 500 内部服务器错误。

## 修复方案

### 1. 移除 Passlib 并使用原生 Bcrypt 替代
鉴于 `passlib` 已经停止维护并存在无法轻易解决的兼容性问题，我们将密码加密和校验的逻辑直接替换为标准的 `bcrypt` 库。
- **依赖更新**：在 `requirements.txt` 中移除了 `passlib[bcrypt]`，并添加了 `bcrypt==4.0.1`。
- **逻辑重构**：修改了 `src/core/security.py` 中的 `get_password_hash` 和 `verify_password` 方法：
  ```python
  import bcrypt

  def verify_password(plain_password: str, hashed_password: str) -> bool:
      return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

  def get_password_hash(password: str) -> str:
      return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
  ```

### 2. 完善注册接口的业务逻辑
在 `src/api/v1/auth.py` 的注册路由中补充了以下逻辑：
- **完整性校验**：新增了对 `email` 和 `phone` 唯一性的检查，出现重复时抛出规范的 `400` 业务异常。
- **数据落库**：将 `phone` 和 `is_active` 存入 `UserModel`，并根据传入的 `role_ids` 查询对应的角色对象并附加到 `user_obj.roles` 关系中。

### 3. 测试代码清理
之前为了规避 `passlib` 的报错，在 `tests/test_api.py` 中加入了针对 `get_password_hash` 的 mock 逻辑。随着底层库的替换，现在可以直接使用真实的哈希函数进行测试，因此清理了所有相关的 mock 代码。

## 经验总结

- **依赖维护**：对于核心的加密库（如 `passlib`），如果社区长期未维护且出现与底层依赖（如 `bcrypt`）的兼容性问题时，应果断考虑迁移到更活跃的替代方案或直接使用底层库的原生 API。
- **异常捕获与校验前置**：在处理涉及数据库唯一约束的字段（如 `email`, `phone`）时，务必在应用层（API 路由中）进行前置的查询校验，避免依赖数据库在 `commit` 阶段抛出 500 异常，这样可以为客户端提供更加清晰和准确的 400 错误提示。
