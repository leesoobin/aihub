from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from aihub.schemas.user import User, UserCreate
from aihub.models.user import UserModel
from aihub.core.database import get_db
from datetime import datetime, timedelta
from typing import List

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/", response_model=List[User])
async def get_all_users(db: Session = Depends(get_db)):
    """모든 사용자 정보를 조회합니다."""
    users = db.query(UserModel).all()
    return users

@router.post("/okta/{okta_id}", response_model=User)
async def record_access(
    okta_id: str,
    user_info: UserCreate,
    db: Session = Depends(get_db)
):
    # 기존 사용자 조회
    existing_user = db.query(UserModel).filter(
        UserModel.okta_id == okta_id
    ).first()

    if existing_user:
        # 마지막 접근 시간이 10분 이내인지 확인
        if datetime.utcnow() - existing_user.access_date < timedelta(minutes=10):
            # 토큰이 아직 유효함
            existing_user.access_date = datetime.utcnow()  # 접근 시간 갱신
            db.commit()
            return existing_user
        else:
            # 새로운 토큰 정보가 있는지 확인
            if user_info.access_token and user_info.refresh_token:
                # 토큰 정보 업데이트
                existing_user.access_token = user_info.access_token
                existing_user.refresh_token = user_info.refresh_token
                existing_user.access_date = datetime.utcnow()
                db.commit()
                return existing_user
            else:
                # 토큰 만료, 새로운 세션 필요
                print("토큰 만료, 새로운 세션 필요")
                raise HTTPException(status_code=401, detail="Token expired")

    # 새로운 사용자 생성
    db_user = UserModel(
        okta_id=okta_id,
        name=user_info.name,
        email=user_info.email,
        access_date=datetime.utcnow(),
        access_token=user_info.access_token,
        refresh_token=user_info.refresh_token
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/validate/{okta_id}", response_model=bool)
async def validate_session(
    okta_id: str,
    db: Session = Depends(get_db)
):
    # 사용자의 마지막 접근 시간 확인
    user = db.query(UserModel).filter(
        UserModel.okta_id == okta_id
    ).first()

    if not user:
        return False

    # 10분 이내 접근이면 유효한 세션으로 간주
    if datetime.utcnow() - user.access_date < timedelta(minutes=10):
        # 접근 시간 갱신
        user.access_date = datetime.utcnow()
        db.commit()
        return True
    
    return False 