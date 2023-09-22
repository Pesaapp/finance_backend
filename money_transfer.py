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
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'completed', 'failed'

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for request input validation
class TransferCreate(BaseModel):
    receiver_email: str
    amount: float

# API Endpoint to Initiate Money Transfer
@app.post("/transfer", response_model=dict)
async def initiate_transfer(data: TransferCreate, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    sender = db.query(User).filter_by(email=current_user_email).first()

    if not sender:
        raise HTTPException(status_code=404, detail="User not found")

    receiver_email = data.receiver_email
    amount = data.amount

    # Check if the receiver exists
    receiver = db.query(User).filter_by(email=receiver_email).first()
    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Check if the sender has sufficient funds
    if sender.balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Perform the money transfer and update balances
    sender.balance -= amount
    receiver.balance += amount

    # Log the transaction
    transaction = Transaction(sender_id=sender.id, receiver_id=receiver.id, amount=amount, date=datetime.now())
    db.add(transaction)
    db.commit()

    return {"message": "Transfer successful"}

# API Endpoint to Get User Transactions
@app.get("/transactions", response_model=dict)
async def get_transactions(current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    transactions = db.query(Transaction).filter_by(sender_id=user.id).all()
    transaction_data = [{'receiver': transaction.receiver.email,
                         'amount': transaction.amount,
                         'date': transaction.date,
                         'status': transaction.status} for transaction in transactions]

    return {'transactions': transaction_data}
