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

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'deposit', 'withdrawal', 'transfer'
    date = Column(DateTime, nullable=False)
    description = Column(String(200), nullable=True)

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    message = Column(String(200), nullable=False)
    date = Column(DateTime, nullable=False)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for request input validation
class TransactionCreate(BaseModel):
    amount: float
    transaction_type: str
    description: str = None

class NotificationCreate(BaseModel):
    message: str

# API Endpoint to Get User Transactions
@app.get("/transactions", response_model=list)
async def get_transactions(current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    transactions = db.query(Transaction).filter_by(user_id=user.id).all()
    transaction_data = [{'amount': transaction.amount,
                         'transaction_type': transaction.transaction_type,
                         'date': transaction.date,
                         'description': transaction.description} for transaction in transactions]

    return transaction_data

# API Endpoint to Get User Notifications
@app.get("/notifications", response_model=list)
async def get_notifications(current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notifications = db.query(Notification).filter_by(user_id=user.id).all()
    notification_data = [{'message': notification.message,
                          'date': notification.date} for notification in notifications]

    return notification_data

# Function to send a notification
def send_notification(user_id: int, message: str, db: Session = Depends(get_db)):
    notification = Notification(user_id=user_id, message=message, date=datetime.now())
    db.add(notification)
    db.commit()

if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
    app.run(debug=True)
