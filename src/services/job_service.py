from sqlalchemy.orm import Session, selectinload
from src.models.business import KnowledgeGraph, JobPosition, job_skills
from src.models.assessment import UserSkillMastery
from src.schemas.business import JobPositionCreate, JobPosition as JobPositionSchema
from src.core.exceptions import BusinessException
from typing import List, Dict, Any

def create_job_position(db: Session, obj_in: JobPositionCreate) -> JobPosition:
    db_obj = JobPosition(
        title=obj_in.title,
        description=obj_in.description,
        level=obj_in.level,
        industry=obj_in.industry
    )
    
    if obj_in.skill_ids:
        skills = db.query(KnowledgeGraph).filter(KnowledgeGraph.id.in_(obj_in.skill_ids)).all()
        db_obj.required_skills = skills
        
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_job_positions(db: Session, skip: int = 0, limit: int = 100) -> List[JobPosition]:
    return db.query(JobPosition).options(selectinload(JobPosition.required_skills)).offset(skip).limit(limit).all()

def get_job_skill_tree(db: Session, job_id: int) -> Dict[str, Any]:
    job = db.query(JobPosition).options(selectinload(JobPosition.required_skills)).filter(JobPosition.id == job_id).first()
    if not job:
        raise BusinessException(code=404, detail="Job Position not found")
        
    # Get required skill IDs
    required_skill_ids = [skill.id for skill in job.required_skills]
    
    # We will return the whole tree but mark required skills
    # First get all root nodes
    roots = db.query(KnowledgeGraph).filter(KnowledgeGraph.parent_id == None).options(selectinload(KnowledgeGraph.children)).all()
    
    def build_tree(node: KnowledgeGraph) -> Dict[str, Any]:
        is_required = node.id in required_skill_ids
        children = [build_tree(child) for child in node.children]
        
        # If any child is required, the parent implicitly becomes part of the required path
        has_required_child = any(c.get("is_required") or c.get("has_required_child") for c in children)
        
        return {
            "id": node.id,
            "concept_name": node.concept_name,
            "description": node.description,
            "is_required": is_required,
            "has_required_child": has_required_child,
            "children": children
        }
        
    tree = [build_tree(root) for root in roots]
    return {
        "job_title": job.title,
        "skill_tree": tree
    }

def calculate_job_match(db: Session, user_id: int, job_id: int) -> float:
    job = db.query(JobPosition).options(selectinload(JobPosition.required_skills)).filter(JobPosition.id == job_id).first()
    if not job or not job.required_skills:
        return 0.0
        
    required_skill_ids = [skill.id for skill in job.required_skills]
    
    # Get user's mastery for these skills
    masteries = db.query(UserSkillMastery).filter(
        UserSkillMastery.user_id == user_id,
        UserSkillMastery.knowledge_graph_id.in_(required_skill_ids)
    ).all()
    
    mastery_map = {m.knowledge_graph_id: m.mastery_level for m in masteries}
    
    # Simple average for now. Could be weighted if job_skills table weights are queried.
    total_score = sum(mastery_map.get(skill_id, 0.0) for skill_id in required_skill_ids)
    max_possible = len(required_skill_ids) * 100.0
    
    if max_possible == 0:
        return 0.0
        
    return round((total_score / max_possible) * 100, 2)
