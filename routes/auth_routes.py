from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models
import schemas
from database import get_db
from utils.security import get_password_hash, verify_password, create_access_token, get_current_user
from config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/signup", response_model=schemas.Token)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_pwd = get_password_hash(user.password)
    
    # Create User
    new_user = models.User(name=user.name, email=user.email, hashed_password=hashed_pwd, role=user.role)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Create profile
    profile = models.UserProfile(user_id=new_user.id, learning_streak=1)
    db.add(profile)
    
    # Create default settings
    default_settings = models.UserSettings(user_id=new_user.id)
    db.add(default_settings)
    
    db.commit()
    
    access_token = create_access_token(
        data={"sub": new_user.email}, 
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update streak
    if db_user.profile:
        today = datetime.utcnow().date()
        last_active = db_user.profile.last_active.date()
        if today > last_active:
            if (today - last_active).days == 1:
                db_user.profile.learning_streak += 1
            elif (today - last_active).days > 1:
                db_user.profile.learning_streak = 1
        db_user.profile.last_active = datetime.utcnow()
        db.commit()
        
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    # Set cookie for page-based templates
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "success", "message": "Successfully logged out"}

@router.post("/google", response_model=schemas.Token)
def google_auth(payload: dict, response: Response, db: Session = Depends(get_db)):
    email = payload.get("email")
    name = payload.get("name", "Google User")
    
    if not email:
        raise HTTPException(status_code=400, detail="Invalid email from OAuth payload")
        
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        # Auto register
        hashed_pwd = get_password_hash("GoogleAuthPass123_SecureSecret")
        db_user = models.User(name=name, email=email, hashed_password=hashed_pwd, role="student")
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Profile & Settings
        profile = models.UserProfile(user_id=db_user.id, learning_streak=1)
        db.add(profile)
        default_settings = models.UserSettings(user_id=db_user.id)
        db.add(default_settings)
        db.commit()
    else:
        # Update streak
        if db_user.profile:
            db_user.profile.learning_streak += 1
            db_user.profile.last_active = datetime.utcnow()
            db.commit()
            
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/verify-otp", response_model=schemas.Token)
def verify_otp(payload: dict, response: Response, db: Session = Depends(get_db)):
    email = payload.get("email")
    otp = payload.get("otp")
    
    # Simulation: Accept any 6 digit numeric code
    if not email or not otp or len(str(otp)) != 6:
        raise HTTPException(status_code=400, detail="Invalid OTP code")
        
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        # Auto register since OTP verified
        hashed_pwd = get_password_hash("OTPAuthPass123_SecureSecret")
        db_user = models.User(name=email.split("@")[0].capitalize(), email=email, hashed_password=hashed_pwd, role="student")
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        profile = models.UserProfile(user_id=db_user.id, learning_streak=1)
        db.add(profile)
        default_settings = models.UserSettings(user_id=db_user.id)
        db.add(default_settings)
        db.commit()
        
    access_token = create_access_token(
        data={"sub": db_user.email},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax"
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/reset-password")
def reset_password(payload: dict, db: Session = Depends(get_db)):
    email = payload.get("email")
    new_password = payload.get("password")
    
    if not email or not new_password:
        raise HTTPException(status_code=400, detail="Email and new password required")
        
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="Email address not found")
        
    db_user.hashed_password = get_password_hash(new_password)
    db.commit()
    return {"status": "success", "message": "Password successfully updated"}

@router.get("/profile", response_model=schemas.UserProfileResponse)
def get_profile(current_user: models.User = Depends(get_current_user)):
    profile = current_user.profile
    return {
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "joined": current_user.created_at,
        "photo_url": profile.photo_url if profile else None,
        "education": profile.education if profile else None,
        "skills": profile.skills if profile else None,
        "achievements": profile.achievements if profile else None,
        "certificates": profile.certificates if profile else None,
        "learning_streak": profile.learning_streak if profile else 0
    }

@router.put("/profile", response_model=schemas.UserProfileResponse)
def update_profile(profile_data: schemas.UserProfileUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    profile = current_user.profile
    if not profile:
        profile = models.UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
    if profile_data.photo_url is not None:
        profile.photo_url = profile_data.photo_url
    if profile_data.education is not None:
        profile.education = profile_data.education
    if profile_data.skills is not None:
        profile.skills = profile_data.skills
    if profile_data.achievements is not None:
        profile.achievements = profile_data.achievements
    if profile_data.certificates is not None:
        profile.certificates = profile_data.certificates
        
    db.commit()
    db.refresh(current_user)
    
    return {
        "name": current_user.name,
        "email": current_user.email,
        "role": current_user.role,
        "joined": current_user.created_at,
        "photo_url": profile.photo_url,
        "education": profile.education,
        "skills": profile.skills,
        "achievements": profile.achievements,
        "certificates": profile.certificates,
        "learning_streak": profile.learning_streak
    }
