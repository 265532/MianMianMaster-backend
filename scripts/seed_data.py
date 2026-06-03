"""
Seed Data Import Script
=======================
将 docs/seed-data/ 目录下的 JSON 数据导入 PostgreSQL 数据库。

使用方式:
    python -m scripts.seed_data          # 导入所有数据
    python -m scripts.seed_data --dry    # 预览模式，不实际写入
    python -m scripts.seed_data --clear  # 清除所有种子数据

依赖关系（插入顺序）:
    第 1 层: roles, users, user_profiles, system_configs, badges, job_positions, knowledge_graphs, courses
    第 2 层: assessments, notifications
    第 3 层: posts, interview_sessions
    第 4 层: comments, user_badges
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect as sa_inspect
from sqlalchemy.orm import Session
from src.db.database import engine, SessionLocal, Base
from src.core.security import get_password_hash

# ============================================================================
# 工具函数
# ============================================================================

SEED_DIR = Path(__file__).parent.parent / "docs" / "seed-data"

# ID 偏移量：种子数据 ID 从 SEED_OFFSET + 原始ID 开始，避免与已有数据冲突
# 例: 原始 ID=1 → 种子 ID=10001
SEED_OFFSET = 10000


def seed_id(original_id: Any) -> int:
    """将原始种子 ID 转换为带偏移的数据库 ID"""
    return safe_int(original_id) + SEED_OFFSET

def load_json(filename: str) -> Any:
    """加载 seed JSON 文件"""
    filepath = SEED_DIR / filename
    if not filepath.exists():
        print(f"  ⚠️  文件不存在: {filepath}")
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """解析 ISO 8601 时间字符串为 datetime 对象"""
    if not dt_str:
        return None
    # 处理多种格式
    for fmt in [
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ]:
        try:
            dt = datetime.strptime(dt_str, fmt)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    print(f"  ⚠️  无法解析时间: {dt_str}")
    return None


def safe_int(value: Any, default: int = 0) -> int:
    """安全转换为整数"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """安全转换为浮点数"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_str(value: Any, default: str = "") -> str:
    """安全转换为字符串"""
    if value is None:
        return default
    return str(value)


# ============================================================================
# 数据导入函数
# ============================================================================

def seed_roles(db: Session, dry_run: bool = False) -> dict:
    """导入角色数据，返回 {name: seed_db_id} 映射"""
    print("\n📋 导入角色数据...")

    # 从 users.json 中提取所有角色
    users_data = load_json("auth/users.json")
    roles_map = {}  # name -> original_id

    for user in users_data:
        for role in user.get("roles", []):
            if role["name"] not in roles_map:
                roles_map[role["name"]] = role["id"]

    # 添加默认角色
    default_roles = [
        {"id": 1, "name": "user", "description": "普通用户"},
        {"id": 2, "name": "admin", "description": "管理员"},
        {"id": 3, "name": "moderator", "description": "版主"},
    ]
    for role in default_roles:
        if role["name"] not in roles_map:
            roles_map[role["name"]] = role["id"]

    # 返回 seed_id 映射: name -> seed_db_id
    result_map = {}
    count = 0
    for name, orig_id in roles_map.items():
        db_id = seed_id(orig_id)
        result_map[name] = db_id

        if dry_run:
            print(f"    [DRY] INSERT role: {name} (id={db_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM roles WHERE name = :name"),
                {"name": name}
            ).fetchone()

            if not existing:
                db.execute(
                    text("""
                        INSERT INTO roles (id, name, description, created_at, updated_at)
                        VALUES (:id, :name, :description, NOW(), NOW())
                    """),
                    {
                        "id": db_id,
                        "name": name,
                        "description": "种子数据角色",
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 角色: {count} 条")
    return result_map


def seed_users(db: Session, roles_map: dict, dry_run: bool = False) -> dict:
    """导入用户数据，返回 {original_id: seed_db_id} 映射"""
    print("\n👤 导入用户数据...")

    users_data = load_json("auth/users.json")

    # 生成默认密码哈希（种子用户密码: Seed@123456）
    default_password = get_password_hash("Seed@123456")

    users_map = {}  # original_id -> seed_db_id
    count = 0

    for user in users_data:
        original_id = user["id"]
        db_user_id = seed_id(original_id)
        users_map[original_id] = db_user_id

        if dry_run:
            print(f"    [DRY] INSERT user: {user['username']} (id={original_id}→{db_user_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM users WHERE id = :id"),
                {"id": db_user_id}
            ).fetchone()

            if not existing:
                db.execute(
                    text("""
                        INSERT INTO users (id, username, email, phone, hashed_password, is_active, created_at, updated_at)
                        VALUES (:id, :username, :email, :phone, :hashed_password, :is_active, :created_at, :updated_at)
                    """),
                    {
                        "id": db_user_id,
                        "username": user["username"],
                        "email": user["email"],
                        "phone": user.get("phone"),
                        "hashed_password": default_password,
                        "is_active": user.get("is_active", True),
                        "created_at": parse_datetime(user.get("created_at")),
                        "updated_at": parse_datetime(user.get("updated_at")),
                    }
                )

                # 创建用户 Profile
                profile = user.get("profile")
                if profile:
                    db.execute(
                        text("""
                            INSERT INTO user_profiles (id, user_id, avatar_url, education, target_position, work_years, experience_points, level, created_at, updated_at)
                            VALUES (:id, :user_id, :avatar_url, :education, :target_position, :work_years, :experience_points, :level, :created_at, :updated_at)
                        """),
                        {
                            "id": seed_id(profile.get("id", original_id)),
                            "user_id": db_user_id,
                            "avatar_url": profile.get("avatar_url", ""),
                            "education": profile.get("education"),
                            "target_position": profile.get("target_position"),
                            "work_years": profile.get("work_years"),
                            "experience_points": profile.get("experience_points", 0),
                            "level": profile.get("level", 1),
                            "created_at": parse_datetime(profile.get("created_at")),
                            "updated_at": parse_datetime(profile.get("updated_at")),
                        }
                    )

                # 关联用户角色（使用偏移后的角色 ID）
                for role in user.get("roles", []):
                    role_name = role.get("name")
                    role_db_id = roles_map.get(role_name) if role_name else None
                    if role_db_id:
                        db.execute(
                            text("""
                                INSERT INTO user_roles (user_id, role_id)
                                VALUES (:user_id, :role_id)
                                ON CONFLICT DO NOTHING
                            """),
                            {"user_id": db_user_id, "role_id": role_db_id}
                        )

                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 用户: {count} 条")
    return users_map


def seed_system_configs(db: Session, dry_run: bool = False) -> int:
    """导入系统配置"""
    print("\n⚙️  导入系统配置...")

    configs = load_json("system/configs.json")
    count = 0

    for config in configs:
        if dry_run:
            print(f"    [DRY] INSERT config: {config['key']}")
        else:
            existing = db.execute(
                text("SELECT id FROM system_configs WHERE key = :key"),
                {"key": config["key"]}
            ).fetchone()

            if not existing:
                # value 需要是 JSON 格式
                value = config["value"]
                if isinstance(value, str):
                    # 尝试解析为 JSON
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        value = {"raw": value}

                db.execute(
                    text("""
                        INSERT INTO system_configs (key, value, description, updated_at)
                        VALUES (:key, CAST(:value AS jsonb), :description, NOW())
                    """),
                    {
                        "key": config["key"],
                        "value": json.dumps(value),
                        "description": config.get("description"),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 系统配置: {count} 条")
    return count


def seed_badges(db: Session, dry_run: bool = False) -> dict:
    """导入徽章数据，返回 {original_id: seed_db_id} 映射"""
    print("\n🏅 导入徽章数据...")

    badges = load_json("learning/badges.json")
    badge_map = {}
    count = 0

    for badge in badges:
        orig_id = badge["id"]
        db_id = seed_id(orig_id)
        badge_map[orig_id] = db_id

        if dry_run:
            print(f"    [DRY] INSERT badge: {badge['name']} (id={orig_id}→{db_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM badges WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                db.execute(
                    text("""
                        INSERT INTO badges (id, name, description, icon_url, condition_type, condition_value, created_at)
                        VALUES (:id, :name, :description, :icon_url, :condition_type, :condition_value, :created_at)
                    """),
                    {
                        "id": db_id,
                        "name": badge["name"],
                        "description": badge.get("description"),
                        "icon_url": badge.get("icon_url"),
                        "condition_type": badge.get("condition_type", "manual"),
                        "condition_value": badge.get("condition_value"),
                        "created_at": parse_datetime(badge.get("created_at")),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 徽章: {count} 条")
    return badge_map


def seed_job_positions(db: Session, dry_run: bool = False) -> dict:
    """导入职位数据，返回 {original_id: seed_db_id} 映射"""
    print("\n💼 导入职位数据...")

    positions = load_json("job/positions.json")
    pos_map = {}
    count = 0

    for pos in positions:
        orig_id = pos["id"]
        db_id = seed_id(orig_id)
        pos_map[orig_id] = db_id

        if dry_run:
            print(f"    [DRY] INSERT job_position: {pos['title']} (id={orig_id}→{db_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM job_positions WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                db.execute(
                    text("""
                        INSERT INTO job_positions (id, title, description, level, industry, created_at, updated_at)
                        VALUES (:id, :title, :description, :level, :industry, :created_at, :updated_at)
                    """),
                    {
                        "id": db_id,
                        "title": pos["title"],
                        "description": pos.get("description"),
                        "level": pos.get("level", "junior"),
                        "industry": pos.get("company"),
                        "created_at": parse_datetime(pos.get("created_at")),
                        "updated_at": parse_datetime(pos.get("updated_at")),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 职位: {count} 条")
    return pos_map


def seed_knowledge_graphs(db: Session, dry_run: bool = False) -> dict:
    """导入知识图谱数据，返回 {original_id: seed_db_id} 映射"""
    print("\n🌳 导入知识图谱数据...")

    skill_tree = load_json("job/skill_tree.json")
    node_map = {}
    count = 0

    def insert_node(node: dict, parent_orig_id: Optional[int] = None):
        nonlocal count
        orig_id = node["id"]
        db_id = seed_id(orig_id)
        node_map[orig_id] = db_id

        # 将 parent 原始 ID 映射为偏移后的 ID
        db_parent_id = node_map.get(parent_orig_id) if parent_orig_id else None

        if dry_run:
            print(f"    [DRY] INSERT knowledge_graph: {node['name']} (id={orig_id}→{db_id}, parent={parent_orig_id}→{db_parent_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM knowledge_graphs WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                db.execute(
                    text("""
                        INSERT INTO knowledge_graphs (id, concept_name, description, parent_id, tags, created_at, updated_at)
                        VALUES (:id, :concept_name, :description, :parent_id, CAST(:tags AS jsonb), NOW(), NOW())
                    """),
                    {
                        "id": db_id,
                        "concept_name": node["name"],
                        "description": node.get("description", node.get("category", "")),
                        "parent_id": db_parent_id,
                        "tags": json.dumps(node.get("tags", [])),
                    }
                )
                count += 1

        # 递归处理子节点
        for child in node.get("children", []):
            insert_node(child, orig_id)

    if isinstance(skill_tree, list):
        for tree in skill_tree:
            insert_node(tree)
    else:
        insert_node(skill_tree)

    if not dry_run:
        db.commit()
    print(f"  ✅ 知识图谱: {count} 条")
    return node_map


def seed_courses(db: Session, dry_run: bool = False) -> dict:
    """导入课程数据，返回 {original_id: seed_db_id} 映射"""
    print("\n📚 导入课程数据...")

    courses = load_json("learning/courses.json")
    course_map = {}
    count = 0

    for course in courses:
        orig_id = course["id"]
        db_id = seed_id(orig_id)
        course_map[orig_id] = db_id

        if dry_run:
            print(f"    [DRY] INSERT course: {course['title']} (id={orig_id}→{db_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM courses WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                db.execute(
                    text("""
                        INSERT INTO courses (id, title, description, level, cover_url, created_at, updated_at)
                        VALUES (:id, :title, :description, :level, :cover_url, :created_at, :updated_at)
                    """),
                    {
                        "id": db_id,
                        "title": course["title"],
                        "description": course.get("description"),
                        "level": course.get("difficulty", "beginner"),
                        "cover_url": course.get("cover_url"),
                        "created_at": parse_datetime(course.get("created_at")),
                        "updated_at": parse_datetime(course.get("updated_at")),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 课程: {count} 条")
    return course_map


def seed_assessments(db: Session, job_positions_map: dict, dry_run: bool = False) -> dict:
    """导入测评数据，返回 {original_id: seed_db_id} 映射"""
    print("\n📝 导入测评数据...")

    assessments = load_json("assessment/assessments.json")
    assessment_map = {}
    count = 0

    for assessment in assessments:
        orig_id = assessment["id"]
        db_id = seed_id(orig_id)
        assessment_map[orig_id] = db_id

        if dry_run:
            print(f"    [DRY] INSERT assessment: {assessment['title']} (id={orig_id}→{db_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM assessments WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                # 映射 job_position_id
                orig_job_id = assessment.get("job_position_id")
                db_job_id = job_positions_map.get(orig_job_id) if orig_job_id else None

                db.execute(
                    text("""
                        INSERT INTO assessments (id, title, description, job_position_id, created_at, updated_at)
                        VALUES (:id, :title, :description, :job_position_id, :created_at, :updated_at)
                    """),
                    {
                        "id": db_id,
                        "title": assessment["title"],
                        "description": assessment.get("description", assessment.get("type", "")),
                        "job_position_id": db_job_id,
                        "created_at": parse_datetime(assessment.get("created_at")),
                        "updated_at": parse_datetime(assessment.get("updated_at")),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 测评: {count} 条")
    return assessment_map


def seed_notifications(db: Session, users_map: dict, dry_run: bool = False) -> int:
    """导入通知数据"""
    print("\n🔔 导入通知数据...")

    notifications = load_json("notification/notifications.json")
    count = 0

    # 默认关联到第一个种子用户
    default_orig_uid = 1
    default_db_uid = users_map.get(default_orig_uid, seed_id(default_orig_uid))

    for notif in notifications:
        orig_id = notif["id"]
        db_id = seed_id(orig_id)

        if dry_run:
            print(f"    [DRY] INSERT notification: {notif['title']} (id={orig_id}→{db_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM notifications WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                # 映射 user_id
                orig_uid = notif.get("user_id", default_orig_uid)
                db_uid = users_map.get(orig_uid, default_db_uid)

                db.execute(
                    text("""
                        INSERT INTO notifications (id, user_id, title, content, type, is_read, created_at)
                        VALUES (:id, :user_id, :title, :content, :type, :is_read, :created_at)
                    """),
                    {
                        "id": db_id,
                        "user_id": db_uid,
                        "title": notif["title"],
                        "content": notif["content"],
                        "type": notif.get("type", "system"),
                        "is_read": notif.get("is_read", False),
                        "created_at": parse_datetime(notif.get("created_at")),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 通知: {count} 条")
    return count


def seed_posts(db: Session, users_map: dict, dry_run: bool = False) -> dict:
    """导入帖子数据，返回 {original_id: seed_db_id} 映射"""
    print("\n📮 导入帖子数据...")

    posts = load_json("community/posts.json")
    post_map = {}
    count = 0

    for post in posts:
        orig_id = post["id"]
        db_id = seed_id(orig_id)
        post_map[orig_id] = db_id

        if dry_run:
            print(f"    [DRY] INSERT post: {post['title'][:30]}... (id={orig_id}→{db_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM posts WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                # 映射 author_id：如果用户不存在，回退到第一个种子用户
                orig_author_id = post.get("author_id", 1)
                db_author_id = users_map.get(orig_author_id)
                if db_author_id is None:
                    db_author_id = users_map.get(1, seed_id(1))

                category = post.get("category", "experience")
                if category not in ["interview_review", "real_questions", "experience"]:
                    category = "experience"

                db.execute(
                    text("""
                        INSERT INTO posts (id, user_id, title, content, category, status, ai_analysis_status, created_at, updated_at)
                        VALUES (:id, :user_id, :title, :content, :category, :status, :ai_analysis_status, :created_at, :updated_at)
                    """),
                    {
                        "id": db_id,
                        "user_id": db_author_id,
                        "title": post["title"],
                        "content": post["content"],
                        "category": category,
                        "status": post.get("status", "published"),
                        "ai_analysis_status": post.get("ai_analysis_status", "completed"),
                        "created_at": parse_datetime(post.get("created_at")),
                        "updated_at": parse_datetime(post.get("updated_at")),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 帖子: {count} 条")
    return post_map


def seed_comments(db: Session, users_map: dict, posts_map: dict, dry_run: bool = False) -> int:
    """导入评论数据"""
    print("\n💬 导入评论数据...")

    comments_data = load_json("community/comments.json")
    count = 0

    # 默认用户
    default_db_uid = users_map.get(1, seed_id(1))

    def _insert_comment(comment: dict, post_orig_id: int) -> None:
        nonlocal count
        orig_id = comment["id"]
        db_id = seed_id(orig_id)

        if dry_run:
            print(f"    [DRY] INSERT comment: id={orig_id}→{db_id}, post={post_orig_id}")
        else:
            existing = db.execute(
                text("SELECT id FROM comments WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                # 映射外键
                db_post_id = posts_map.get(post_orig_id, seed_id(post_orig_id))
                orig_author_id = comment.get("author_id", 1)
                db_author_id = users_map.get(orig_author_id, default_db_uid)

                db.execute(
                    text("""
                        INSERT INTO comments (id, post_id, user_id, parent_id, content, created_at, updated_at)
                        VALUES (:id, :post_id, :user_id, :parent_id, :content, :created_at, :updated_at)
                    """),
                    {
                        "id": db_id,
                        "post_id": db_post_id,
                        "user_id": db_author_id,
                        "parent_id": None,
                        "content": comment["content"],
                        "created_at": parse_datetime(comment.get("created_at")),
                        "updated_at": parse_datetime(comment.get("updated_at")),
                    }
                )
                count += 1

    # comments.json 可能是 {post_id: [comments]} 字典格式
    if isinstance(comments_data, dict):
        for post_id_str, comments in comments_data.items():
            post_orig_id = safe_int(post_id_str)
            for comment in comments:
                _insert_comment(comment, post_orig_id)
    elif isinstance(comments_data, list):
        for comment in comments_data:
            post_orig_id = comment.get("post_id", 1)
            _insert_comment(comment, post_orig_id)

    if not dry_run:
        db.commit()
    print(f"  ✅ 评论: {count} 条")
    return count


def seed_user_badges(db: Session, users_map: dict, badges_map: dict, dry_run: bool = False) -> int:
    """导入用户徽章数据"""
    print("\n🎖️  导入用户徽章数据...")

    user_badges = load_json("learning/user_badges.json")
    count = 0

    # 默认关联到第一个种子用户
    default_db_uid = users_map.get(1, seed_id(1))

    for ub in user_badges:
        orig_id = ub["id"]
        db_id = seed_id(orig_id)

        if dry_run:
            print(f"    [DRY] INSERT user_badge: id={orig_id}→{db_id}, badge={ub.get('badge_id')}")
        else:
            existing = db.execute(
                text("SELECT id FROM user_badges WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                # 映射外键
                orig_badge_id = ub["badge_id"]
                db_badge_id = badges_map.get(orig_badge_id, seed_id(orig_badge_id))
                orig_uid = ub.get("user_id", 1)
                db_uid = users_map.get(orig_uid, default_db_uid)

                db.execute(
                    text("""
                        INSERT INTO user_badges (id, user_id, badge_id, awarded_at, tx_hash)
                        VALUES (:id, :user_id, :badge_id, :awarded_at, :tx_hash)
                    """),
                    {
                        "id": db_id,
                        "user_id": db_uid,
                        "badge_id": db_badge_id,
                        "awarded_at": parse_datetime(ub.get("awarded_at")),
                        "tx_hash": ub.get("tx_hash"),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 用户徽章: {count} 条")
    return count


def seed_interview_sessions(db: Session, users_map: dict, dry_run: bool = False) -> int:
    """导入面试会话数据"""
    print("\n🎤 导入面试会话数据...")

    sessions = load_json("interview/sessions.json")
    count = 0

    default_db_uid = users_map.get(1, seed_id(1))

    for idx, session in enumerate(sessions, 1):
        # DB 中 id 是 Integer，JSON 中 id 是字符串 "session-001"
        # 使用 seed_id(idx) 作为 DB 主键
        orig_session_id = session["id"]
        db_id = seed_id(idx)

        if dry_run:
            print(f"    [DRY] INSERT interview_session: {orig_session_id} (db_id={db_id})")
        else:
            existing = db.execute(
                text("SELECT id FROM interview_sessions WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                orig_uid = session.get("user_id", 1)
                db_uid = users_map.get(orig_uid, default_db_uid)

                status_map = {
                    "completed": "completed",
                    "in_progress": "in_progress",
                    "scheduled": "scheduled",
                    "cancelled": "failed",
                }
                status = status_map.get(session.get("status", "scheduled"), "scheduled")

                db.execute(
                    text("""
                        INSERT INTO interview_sessions (id, candidate_id, status, score, feedback, start_time, end_time, created_at)
                        VALUES (:id, :candidate_id, :status, :score, :feedback, :start_time, :end_time, :created_at)
                    """),
                    {
                        "id": db_id,
                        "candidate_id": db_uid,
                        "status": status,
                        "score": session.get("total_score"),
                        "feedback": session.get("feedback"),
                        "start_time": parse_datetime(session.get("started_at")),
                        "end_time": parse_datetime(session.get("ended_at")),
                        "created_at": parse_datetime(session.get("created_at")),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 面试会话: {count} 条")
    return count


def seed_assessment_results(db: Session, users_map: dict, assessments_map: dict, dry_run: bool = False) -> int:
    """导入测评结果数据"""
    print("\n📊 导入测评结果数据...")

    results = load_json("assessment/results.json")
    count = 0

    default_db_uid = users_map.get(1, seed_id(1))

    for result in results:
        orig_id = result["id"]
        db_id = seed_id(orig_id)

        if dry_run:
            print(f"    [DRY] INSERT assessment_result: id={orig_id}→{db_id}")
        else:
            existing = db.execute(
                text("SELECT id FROM user_assessment_records WHERE id = :id"),
                {"id": db_id}
            ).fetchone()

            if not existing:
                orig_uid = result.get("user_id", 1)
                db_uid = users_map.get(orig_uid, default_db_uid)
                orig_assess_id = result["assessment_id"]
                db_assess_id = assessments_map.get(orig_assess_id, seed_id(orig_assess_id))

                db.execute(
                    text("""
                        INSERT INTO user_assessment_records (id, user_id, assessment_id, total_score, details, created_at)
                        VALUES (:id, :user_id, :assessment_id, :total_score, CAST(:details AS jsonb), :created_at)
                    """),
                    {
                        "id": db_id,
                        "user_id": db_uid,
                        "assessment_id": db_assess_id,
                        "total_score": result.get("score", 0),
                        "details": json.dumps(result.get("details", {})),
                        "created_at": parse_datetime(result.get("created_at")),
                    }
                )
                count += 1

    if not dry_run:
        db.commit()
    print(f"  ✅ 测评结果: {count} 条")
    return count


# ============================================================================
# 主函数
# ============================================================================

def clear_seed_data(db: Session):
    """清除所有种子数据（按依赖逆序，仅清除 SEED_OFFSET 以上 ID 的数据）"""
    print("\n🗑️  清除种子数据...")

    # 表及对应 ID 列，按依赖逆序排列
    tables_with_id = [
        # 第 4 层
        ("user_assessment_records", "id"),
        ("user_badges", "id"),
        ("user_wrong_questions", "id"),
        ("user_question_collections", "id"),
        ("user_learning_progress", "id"),
        ("comments", "id"),
        ("post_likes", "id"),
        ("posts", "id"),
        # 第 3 层
        ("notifications", "id"),
        ("interview_sessions", "id"),
        # 第 2 层
        ("assessments", "id"),
        # 第 1 层
        ("user_roles", "user_id"),
        ("user_profiles", "id"),
        ("courses", "id"),
        ("knowledge_graphs", "id"),
        ("job_positions", "id"),
        ("badges", "id"),
        ("system_configs", "id"),
        ("users", "id"),
        ("roles", "id"),
    ]

    for table, id_col in tables_with_id:
        try:
            db.execute(text(f"DELETE FROM {table} WHERE {id_col} >= {SEED_OFFSET}"))
            print(f"  🗑️  清除 {table}")
        except Exception as e:
            print(f"  ⚠️  清除 {table} 失败: {e}")

    # 清除 interview_sessions（ID 是字符串格式）
    try:
        db.execute(text("DELETE FROM interview_sessions WHERE id LIKE 'session-%'"))
    except Exception as e:
        print(f"  ⚠️  清除 interview_sessions 失败: {e}")

    db.commit()
    print("  ✅ 清除完成")


def main():
    """主入口"""
    # 解析命令行参数
    dry_run = "--dry" in sys.argv
    clear_mode = "--clear" in sys.argv

    print("=" * 60)
    print("🌱 MianMianMaster Seed Data Import")
    print("=" * 60)

    if dry_run:
        print("📋 模式: 预览 (DRY RUN)")
    elif clear_mode:
        print("📋 模式: 清除数据")
    else:
        print("📋 模式: 导入数据")

    print(f"📂 数据目录: {SEED_DIR}")

    # 检查数据目录
    if not SEED_DIR.exists():
        print(f"\n❌ 数据目录不存在: {SEED_DIR}")
        sys.exit(1)

    # 创建数据库会话
    db = SessionLocal()

    try:
        if clear_mode:
            clear_seed_data(db)
            return

        # 按依赖顺序导入
        print("\n" + "=" * 60)
        print("📥 开始导入数据...")
        print("=" * 60)

        # 第 1 层：无依赖，返回 ID 映射表供后续层使用
        roles_map = seed_roles(db, dry_run)
        users_map = seed_users(db, roles_map, dry_run)
        seed_system_configs(db, dry_run)
        badges_map = seed_badges(db, dry_run)
        job_positions_map = seed_job_positions(db, dry_run)
        knowledge_graphs_map = seed_knowledge_graphs(db, dry_run)
        courses_map = seed_courses(db, dry_run)

        # 第 2 层：依赖第 1 层的外键
        assessments_map = seed_assessments(db, job_positions_map, dry_run)
        seed_notifications(db, users_map, dry_run)

        # 第 3 层：依赖第 2 层的外键
        posts_map = seed_posts(db, users_map, dry_run)
        seed_interview_sessions(db, users_map, dry_run)

        # 第 4 层：依赖第 3 层的外键
        seed_comments(db, users_map, posts_map, dry_run)
        seed_user_badges(db, users_map, badges_map, dry_run)
        seed_assessment_results(db, users_map, assessments_map, dry_run)

        print("\n" + "=" * 60)
        print("🎉 Seed 数据导入完成!")
        print("=" * 60)
        print("\n📌 提示:")
        print("   - 种子用户密码: Seed@123456")
        print("   - 使用 --dry 参数可预览导入内容")
        print("   - 使用 --clear 参数可清除所有种子数据")

    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()