from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List
from app.models.user import User
from app.schemas.user import UserRequest, UserResponse
from app.schemas.auth import PasswordResetRequest
from app.utils.security import hash_password
from app.services.audit_log import AuditLogService

class UserService:
    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        return db.query(User).all()

    @staticmethod
    def create_user(db: Session, request: UserRequest, current_user: str, current_role: str, ip: str) -> User:
        if db.query(User).filter(User.username == request.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        if request.email and db.query(User).filter(User.email == request.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )

        hashed = hash_password(request.password)
        user = User(
            username=request.username,
            password=hashed,
            full_name=request.fullName,
            email=request.email,
            role=request.role,
            active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        AuditLogService.log_action(
            db=db,
            action="CREATE_USER",
            module="USER",
            description=f"Created user {user.username} with role {user.role}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )
        return user

    @staticmethod
    def update_user(db: Session, user_id: int, request: UserRequest, current_user: str, current_role: str, ip: str) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if request.fullName is not None:
            user.full_name = request.fullName
        if request.email is not None:
            user.email = request.email
        if request.role is not None:
            user.role = request.role
        if request.active is not None:
            user.active = request.active

        db.commit()
        db.refresh(user)

        AuditLogService.log_action(
            db=db,
            action="UPDATE_USER",
            module="USER",
            description=f"Updated user {user.username}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )
        return user

    @staticmethod
    def reset_password(db: Session, user_id: int, request: PasswordResetRequest, current_user: str, current_role: str, ip: str):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.password = hash_password(request.newPassword)
        db.commit()

        AuditLogService.log_action(
            db=db,
            action="RESET_PASSWORD",
            module="USER",
            description=f"Reset password for user {user.username}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )

    @staticmethod
    def delete_user(db: Session, user_id: int, current_user: str, current_role: str, ip: str):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Prevent owner from deleting their own account
        if user.username == current_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete your own account"
            )

        # Hard delete user record
        username_deleted = user.username
        db.delete(user)
        db.commit()

        AuditLogService.log_action(
            db=db,
            action="DELETE_USER",
            module="USER",
            description=f"Deleted user {username_deleted} from database",
            username=current_user,
            role=current_role,
            ip_address=ip
        )

