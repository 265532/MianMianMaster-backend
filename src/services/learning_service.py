from sqlalchemy.orm import Session
from src.models.learning import Course, CourseMaterial, UserLearningProgress, UserQuestionCollection, UserWrongQuestion, Badge, UserBadge
from src.schemas import learning as schemas
from src.core.exceptions import BusinessException

class LearningService:

    # ================= Course & Materials =================
    def create_course(self, db: Session, course_in: schemas.CourseCreate) -> Course:
        db_course = Course(**course_in.model_dump())
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        return db_course

    def get_courses(self, db: Session, skip: int = 0, limit: int = 10):
        return db.query(Course).offset(skip).limit(limit).all()

    def get_course(self, db: Session, course_id: int) -> Course:
        course = db.query(Course).filter(Course.id == course_id).first()
        if not course:
            raise BusinessException(code=404, detail="Course not found")
        return course

    def add_material_to_course(self, db: Session, material_in: schemas.CourseMaterialCreate) -> CourseMaterial:
        # Check course exists
        self.get_course(db, material_in.course_id)
        
        # Check knowledge_graph_id if provided
        if material_in.knowledge_graph_id:
            from src.models.business import KnowledgeGraph
            kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == material_in.knowledge_graph_id).first()
            if not kg:
                raise BusinessException(code=404, detail="Knowledge graph not found")
                
        db_material = CourseMaterial(**material_in.model_dump())
        db.add(db_material)
        db.commit()
        db.refresh(db_material)
        return db_material

    # ================= Progress =================
    def update_learning_progress(self, db: Session, user_id: int, course_id: int, material_id: int, progress_in: schemas.UserLearningProgressUpdate) -> UserLearningProgress:
        progress = db.query(UserLearningProgress).filter(
            UserLearningProgress.user_id == user_id,
            UserLearningProgress.material_id == material_id
        ).first()

        if progress:
            progress.progress_percent = progress_in.progress_percent
            progress.is_completed = progress_in.is_completed
        else:
            progress = UserLearningProgress(
                user_id=user_id,
                course_id=course_id,
                material_id=material_id,
                progress_percent=progress_in.progress_percent,
                is_completed=progress_in.is_completed
            )
            db.add(progress)
        
        db.flush() # flush to get updated states
        
        # Check if course is fully completed
        materials_count = db.query(CourseMaterial).filter(CourseMaterial.course_id == course_id).count()
        completed_count = db.query(UserLearningProgress).filter(
            UserLearningProgress.user_id == user_id,
            UserLearningProgress.course_id == course_id,
            UserLearningProgress.is_completed == True
        ).count()
        
        if materials_count > 0 and materials_count == completed_count:
            # Trigger Gamification Hook: Course completed
            badge = db.query(Badge).filter(
                Badge.condition_type == 'course_completed',
                Badge.condition_value == str(course_id)
            ).first()
            if badge:
                self.award_badge(db, user_id, badge.id)
                
            # Add experience points
            from src.models.user import UserProfile
            profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            if profile:
                profile.experience_points += 50
                if profile.experience_points >= profile.level * 100:
                    profile.level += 1
        
        db.commit()
        db.refresh(progress)
        return progress

    def get_user_progress(self, db: Session, user_id: int, course_id: int):
        return db.query(UserLearningProgress).filter(
            UserLearningProgress.user_id == user_id,
            UserLearningProgress.course_id == course_id
        ).all()

    # ================= Question Bank =================
    def add_to_collection(self, db: Session, user_id: int, collection_in: schemas.QuestionCollectionCreate) -> UserQuestionCollection:
        collection = db.query(UserQuestionCollection).filter(
            UserQuestionCollection.user_id == user_id,
            UserQuestionCollection.question_id == collection_in.question_id
        ).first()
        
        if collection:
            collection.notes = collection_in.notes
        else:
            collection = UserQuestionCollection(
                user_id=user_id,
                question_id=collection_in.question_id,
                notes=collection_in.notes
            )
            db.add(collection)
        
        db.commit()
        db.refresh(collection)
        return collection

    def get_collections(self, db: Session, user_id: int, skip: int = 0, limit: int = 10):
        return db.query(UserQuestionCollection).filter(UserQuestionCollection.user_id == user_id).offset(skip).limit(limit).all()

    def record_wrong_question(self, db: Session, user_id: int, wrong_in: schemas.WrongQuestionCreate) -> UserWrongQuestion:
        record = db.query(UserWrongQuestion).filter(
            UserWrongQuestion.user_id == user_id,
            UserWrongQuestion.question_id == wrong_in.question_id
        ).first()

        if record:
            record.wrong_answer = wrong_in.wrong_answer
            record.answer_count += 1
            record.is_mastered = False
        else:
            record = UserWrongQuestion(
                user_id=user_id,
                question_id=wrong_in.question_id,
                wrong_answer=wrong_in.wrong_answer
            )
            db.add(record)
        
        db.commit()
        db.refresh(record)
        return record

    def get_wrong_questions(self, db: Session, user_id: int, skip: int = 0, limit: int = 10):
        return db.query(UserWrongQuestion).filter(UserWrongQuestion.user_id == user_id).offset(skip).limit(limit).all()

    def mark_wrong_question_mastered(self, db: Session, user_id: int, question_id: int):
        record = db.query(UserWrongQuestion).filter(
            UserWrongQuestion.user_id == user_id,
            UserWrongQuestion.question_id == question_id
        ).first()
        if not record:
            raise BusinessException(code=404, detail="Wrong question record not found")
        record.is_mastered = True
        db.commit()
        return record

    # ================= Badges =================
    def create_badge(self, db: Session, badge_in: schemas.BadgeCreate) -> Badge:
        badge = Badge(**badge_in.model_dump())
        db.add(badge)
        db.commit()
        db.refresh(badge)
        return badge

    def get_badges(self, db: Session, skip: int = 0, limit: int = 10):
        return db.query(Badge).offset(skip).limit(limit).all()

    def award_badge(self, db: Session, user_id: int, badge_id: int) -> UserBadge:
        existing = db.query(UserBadge).filter(UserBadge.user_id == user_id, UserBadge.badge_id == badge_id).first()
        if existing:
            return existing
        user_badge = UserBadge(user_id=user_id, badge_id=badge_id)
        db.add(user_badge)
        db.commit()
        db.refresh(user_badge)
        return user_badge

    def get_user_badges(self, db: Session, user_id: int):
        return db.query(UserBadge).filter(UserBadge.user_id == user_id).all()

learning_service = LearningService()
