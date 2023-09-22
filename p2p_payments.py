from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import Session, sessionmaker
from pydantic import BaseModel
from datetime import datetime
from passlib.hash import bcrypt  # Added for password hashing

app = FastAPI()

# Database Configuration
DATABASE_URL = "mysql://your_db_user:your_db_password@localhost/your_db_name"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database Models
class User(BaseModel):
    # ... existing User model ...
    password_hash: str

class Transaction(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    amount: float
    date: datetime
    status: str

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Pydantic model for request input validation
class MoneySendRequest(BaseModel):
    receiver_email: str
    amount: float

class MoneyRequestRequest(BaseModel):
    receiver_email: str
    amount: float

# API Endpoint to Send Money
@app.post("/send_money")
async def send_money(request_data: MoneySendRequest, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    sender = db.query(User).filter_by(email=current_user_email).first()

    if not sender:
        raise HTTPException(status_code=404, detail="User not found")

    receiver = db.query(User).filter_by(email=request_data.receiver_email).first()

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    if sender.balance < request_data.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Perform the money transfer and update balances
    sender.balance -= request_data.amount
    receiver.balance += request_data.amount

    # Log the transaction
    transaction = Transaction(
        sender_id=sender.id,
        receiver_id=receiver.id,
        amount=request_data.amount,
        date=datetime.now(),
        status='completed'
    )

    db.add(transaction)
    db.commit()

    return {'message': 'Money sent successfully'}

# API Endpoint to Request Money
@app.post("/request_money")
async def request_money(request_data: MoneyRequestRequest, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    sender = db.query(User).filter_by(email=current_user_email).first()

    if not sender:
        raise HTTPException(status_code=404, detail="User not found")

    receiver = db.query(User).filter_by(email=request_data.receiver_email).first()

    if not receiver:
        raise HTTPException(status_code=404, detail="Receiver not found")

    # Create a money request record
    # This could involve storing the request in the database and notifying the receiver

    return {'message': 'Money request sent successfully'}

# API Endpoint to Get User Transactions
@app.get("/transactions", response_model=list)
async def get_transactions(current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    transactions = db.query(Transaction).filter_by(sender_id=user.id).all()
    transaction_data = [{'receiver': transaction.receiver.email,
                         'amount': transaction.amount,
                         'date': transaction.date,
                         'status': transaction.status} for transaction in transactions]

    return transaction_data

if __name__ == '__main__':
    app.run(debug=True)
