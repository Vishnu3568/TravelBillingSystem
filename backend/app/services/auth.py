from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest
from app.utils.security import verify_password, hash_password, create_access_token
from app.services.audit_log import AuditLogService

class AuthService:
    @staticmethod
    def login(db: Session, request: LoginRequest, ip: str) -> LoginResponse:
        username = request.username.strip()
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        # Check password matching (verifies against hashed value)
        encoded_password = user.password.strip() if user.password else ""
        if not verify_password(request.password, encoded_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password"
            )

        role = user.role.strip().upper() if user.role else "EMPLOYEE"
        
        # Generate JWT token
        token = create_access_token(username=user.username, role=role)
        
        # Log LOGIN action
        AuditLogService.log_action(
            db=db,
            action="LOGIN",
            module="AUTH",
            description=f"User {username} logged in successfully",
            username=user.username,
            role=role,
            ip_address=ip
        )
        
        return LoginResponse(
            token=token,
            tokenType="Bearer",
            username=user.username,
            role=role
        )

    @staticmethod
    def register(db: Session, request: RegisterRequest, current_user: str, current_role: str, ip: str) -> User:
        if db.query(User).filter(User.username == request.username).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is already taken"
            )
        if db.query(User).filter(User.email == request.email).first():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is already taken"
            )

        user = User(
            username=request.username,
            password=hash_password(request.password),
            email=request.email,
            role=request.role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Log registration
        AuditLogService.log_action(
            db=db,
            action="REGISTER_USER",
            module="AUTH",
            description=f"Registered user {user.username} with role {user.role}",
            username=current_user,
            role=current_role,
            ip_address=ip
        )
        return user
