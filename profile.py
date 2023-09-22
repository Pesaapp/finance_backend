from fastapi import FastAPI, HTTPException, Depends, Form, UploadFile
from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel
from datetime import date
from sqlalchemy.exc import IntegrityError
import os  # For file operations

app = FastAPI()

# Database Configuration
DATABASE_URL = "mysql://your_db_user:your_db_password@localhost/your_db_name"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Models
class User(BaseModel):
    # ... existing User model ...

class UserProfile(BaseModel):
    id: int
    user_id: int
    full_name: str
    date_of_birth: date
    address: str
    profile_picture: str
    privacy_setting: str

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for request input validation
class ProfileCreateRequest(BaseModel):
    full_name: str
    date_of_birth: date
    address: str
    privacy_setting: str

class ProfileUpdateRequest(BaseModel):
    full_name: str
    date_of_birth: date
    address: str
    privacy_setting: str

# API Endpoint to Manage Profile
@app.post("/profile", response_model=UserProfile)
@app.put("/profile", response_model=UserProfile)
async def manage_profile(
    request_data: ProfileCreateRequest if request.method == 'POST' else ProfileUpdateRequest,
    profile_picture: UploadFile = Form(None),
    current_user_email: str = Depends(get_jwt_identity),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.method == 'POST':
        # Create a new user profile
        full_name = request_data.full_name
        date_of_birth = request_data.date_of_birth
        address = request_data.address

        # Handle profile picture upload
        profile_picture_path = None
        if profile_picture:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_picture.filename)
            with open(file_path, "wb") as file:
                file.write(profile_picture.file.read())
            profile_picture_path = file_path

        privacy_setting = request_data.privacy_setting

        profile = UserProfile(
            user_id=user.id,
            full_name=full_name,
            date_of_birth=date_of_birth,
            address=address,
            profile_picture=profile_picture_path,
            privacy_setting=privacy_setting
        )

        try:
            db.add(profile)
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(status_code=400, detail="Profile already exists")

        return profile

    elif request.method == 'PUT':
        # Update the existing user profile
        full_name = request_data.full_name
        date_of_birth = request_data.date_of_birth
        address = request_data.address

        # Handle profile picture update
        profile_picture_path = None
        if profile_picture:
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], profile_picture.filename)
            with open(file_path, "wb") as file:
                file.write(profile_picture.file.read())
            profile_picture_path = file_path

        privacy_setting = request_data.privacy_setting

        profile = db.query(UserProfile).filter_by(user_id=user.id).first()
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")

        profile.full_name = full_name
        profile.date_of_birth = date_of_birth
        profile.address = address

        # Update profile picture and privacy setting
        if profile_picture_path:
            profile.profile_picture = profile_picture_path
        profile.privacy_setting = privacy_setting

        db.commit()

        return profile

if __name__ == '__main__':
    app.run(debug=True)
