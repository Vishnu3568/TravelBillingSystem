import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.learning import ReviewerStatistics

logger = logging.getLogger("feedback_processor")

class FeedbackProcessor:
    @staticmethod
    def get_or_create_reviewer_stats(db: Session, username: str) -> ReviewerStatistics:
        """
        Retrieves the reviewer statistics for the given reviewer username, or creates it.
        """
        if not username:
            username = "System Reviewer"
        stats = db.query(ReviewerStatistics).filter(ReviewerStatistics.reviewer_username == username).first()
        if not stats:
            stats = ReviewerStatistics(
                reviewer_username=username,
                total_reviews=0,
                total_edits=0,
                total_undos=0,
                total_restores=0,
                updated_at=datetime.utcnow()
            )
            db.add(stats)
            db.commit()
            db.refresh(stats)
        return stats

    @staticmethod
    def process_reviewer_action(db: Session, username: str, action_type: str) -> ReviewerStatistics:
        """
        Logs a reviewer action to keep track of system statistics.
        action_types: 'APPROVE', 'REJECT', 'EDIT', 'UNDO', 'RESTORE'
        """
        stats = FeedbackProcessor.get_or_create_reviewer_stats(db, username)
        
        action_upper = action_type.strip().upper()
        if action_upper in ("APPROVE", "REJECT", "SAVE"):
            stats.total_reviews += 1
        elif action_upper == "EDIT":
            stats.total_edits += 1
        elif action_upper == "UNDO":
            stats.total_undos += 1
        elif action_upper == "RESTORE":
            stats.total_restores += 1
            
        stats.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(stats)
        logger.info(f"Logged reviewer interaction: user={username}, action={action_upper}")
        return stats
