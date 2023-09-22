from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

app = FastAPI()

# Database Configuration
DATABASE_URL = "mysql://your_db_user:your_db_password@localhost/your_db_name"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Models
class User(Base):
    __tablename__ = "users"
    # ... existing User model ...

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    account_number = Column(String(50), nullable=False)
    bank_name = Column(String(100), nullable=False)
    is_verified = Column(Boolean, default=False)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoint to Link Bank Account
@app.post("/link_bank_account", response_model=dict)
async def link_bank_account(data: dict, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    account_number = data.get('account_number')
    bank_name = data.get('bank_name')

    # Simulate integration with a hypothetical banking API
    # This would typically involve making API calls, authentication, and verification steps
    # For this example, we assume a successful verification process

    # Assuming a successful verification process
    bank_account = BankAccount(user_id=user.id, account_number=account_number, bank_name=bank_name, is_verified=True)

    try:
        db.add(bank_account)
        db.commit()

        return {"message": "Bank account linked and verified successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")
