from sqlalchemy.orm import Session
from src.models.assessment import Assessment, Question, UserAssessmentRecord, UserSkillMastery
from src.schemas.assessment import AssessmentCreate, AssessmentSubmitRequest
from src.core.exceptions import BusinessException
from typing import List, Dict, Any
from datetime import datetime

def create_assessment(db: Session, obj_in: AssessmentCreate) -> Assessment:
    assessment = Assessment(
        title=obj_in.title,
        description=obj_in.description,
        job_position_id=obj_in.job_position_id
    )
    db.add(assessment)
    db.flush()
    
    for q_in in obj_in.questions:
        q = Question(
            assessment_id=assessment.id,
            knowledge_graph_id=q_in.knowledge_graph_id,
            question_type=q_in.question_type,
            content=q_in.content,
            options=q_in.options,
            correct_answer=q_in.correct_answer,
            score_weight=q_in.score_weight
        )
        db.add(q)
        
    db.commit()
    db.refresh(assessment)
    return assessment

def submit_assessment(db: Session, user_id: int, request: AssessmentSubmitRequest) -> UserAssessmentRecord:
    assessment = db.query(Assessment).filter(Assessment.id == request.assessment_id).first()
    if not assessment:
        raise BusinessException(code=404, detail="Assessment not found")
        
    questions = db.query(Question).filter(Question.assessment_id == request.assessment_id).all()
    q_map = {q.id: q for q in questions}
    
    total_score = 0.0
    details = []
    
    # Tracking skill updates: skill_id -> {score, max}
    skill_updates: Dict[int, Dict[str, float]] = {}
    
    for ans in request.answers:
        q = q_map.get(ans.question_id)
        if not q:
            continue
            
        is_correct = False
        earned_score = 0.0
        
        # Simple evaluation logic
        if q.question_type == "single_choice":
            if ans.answer == q.correct_answer:
                is_correct = True
                earned_score = q.score_weight
        elif q.question_type == "multi_choice":
            if set(ans.answer) == set(q.correct_answer):
                is_correct = True
                earned_score = q.score_weight
        # Add text evaluation via LLM later
        
        total_score += earned_score
        details.append({
            "question_id": q.id,
            "user_answer": ans.answer,
            "is_correct": is_correct,
            "earned_score": earned_score
        })
        
        # Track skill performance
        if q.knowledge_graph_id:
            if q.knowledge_graph_id not in skill_updates:
                skill_updates[q.knowledge_graph_id] = {"earned": 0.0, "total": 0.0}
            skill_updates[q.knowledge_graph_id]["earned"] += earned_score
            skill_updates[q.knowledge_graph_id]["total"] += q.score_weight
            
    # Save Record
    record = UserAssessmentRecord(
        user_id=user_id,
        assessment_id=request.assessment_id,
        total_score=total_score,
        details={"answers": details}
    )
    db.add(record)
    
    # Update Skill Mastery
    for skill_id, stats in skill_updates.items():
        if stats["total"] > 0:
            percentage = (stats["earned"] / stats["total"]) * 100
            
            mastery = db.query(UserSkillMastery).filter(
                UserSkillMastery.user_id == user_id,
                UserSkillMastery.knowledge_graph_id == skill_id
            ).first()
            
            if mastery:
                # Simple moving average for mastery
                mastery.mastery_level = (mastery.mastery_level + percentage) / 2
                mastery.last_assessed_at = datetime.utcnow()
            else:
                mastery = UserSkillMastery(
                    user_id=user_id,
                    knowledge_graph_id=skill_id,
                    mastery_level=percentage
                )
                db.add(mastery)
                
    # Trigger Gamification Hook: Assessment score > 80
    max_possible_score = sum([q.score_weight for q in questions])
    if max_possible_score > 0 and (total_score / max_possible_score) >= 0.8:
        from src.models.learning import Badge, UserBadge
        badge = db.query(Badge).filter(
            Badge.condition_type == 'score_reached',
            Badge.condition_value == str(request.assessment_id)
        ).first()
        if badge:
            existing = db.query(UserBadge).filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge.id).first()
            if not existing:
                db.add(UserBadge(user_id=user_id, badge_id=badge.id))
                
                # Add experience points
                from src.models.user import UserProfile
                profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
                if profile:
                    profile.experience_points += 100
                    if profile.experience_points >= profile.level * 100:
                        profile.level += 1

    db.commit()
    db.refresh(record)
    return record
