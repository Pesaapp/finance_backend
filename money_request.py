from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from datetime import datetime

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

class MoneyRequest(Base):
    __tablename__ = "money_requests"
    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'completed', 'cancelled'
    reminder_date = Column(DateTime, nullable=True)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for request input validation
class MoneyRequestCreate(BaseModel):
    recipient_email: str
    amount: float
    reminder_date: datetime

# API Endpoint to Request Money
@app.post("/money/request", response_model=dict)
async def request_money(data: MoneyRequestCreate, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    requester = db.query(User).filter_by(email=current_user_email).first()

    if not requester:
        raise HTTPException(status_code=404, detail="User not found")

    recipient_email = data.recipient_email
    amount = data.amount
    reminder_date = data.reminder_date

    # Check if the recipient exists
    recipient = db.query(User).filter_by(email=recipient_email).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Create a money request record
    money_request = MoneyRequest(
        requester_id=requester.id,
        recipient_id=recipient.id,
        amount=amount,
        status='pending',
        reminder_date=reminder_date,
    )

    try:
        db.add(money_request)
        db.commit()
        return {"message": "Money request sent successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Money request failed")

# API Endpoint to Get Money Requests
@app.get("/money/requests", response_model=dict)
async def get_money_requests(current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    money_requests = db.query(MoneyRequest).filter_by(requester_id=user.id).all()
    request_data = [{'recipient': request.recipient.email,
                     'amount': request.amount,
                     'status': request.status,
                     'reminder_date': request.reminder_date} for request in money_requests]

    return {'money_requests': request_data}
