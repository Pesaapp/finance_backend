from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
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
    wallet_balance = Column(Float, default=0.0)

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'deposit' or 'withdrawal'
    date = Column(DateTime, nullable=False)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoint to Get Wallet Balance
@app.get("/wallet/balance", response_model=dict)
async def get_wallet_balance(current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"balance": user.wallet_balance}

# API Endpoint to Deposit Funds to Wallet
@app.post("/wallet/deposit", response_model=dict)
async def deposit_to_wallet(data: dict, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    amount = data.get('amount')

    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    # Implement logic to add funds to the wallet
    user.wallet_balance += amount

    # Log the transaction securely
    try:
        transaction = WalletTransaction(
            user_id=user.id,
            amount=amount,
            transaction_type='deposit',
            date=datetime.now()
        )
        db.add(transaction)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed")

    return {"message": "Funds added to wallet successfully"}

# API Endpoint to Withdraw Funds from Wallet
@app.post("/wallet/withdraw", response_model=dict)
async def withdraw_from_wallet(data: dict, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    amount = data.get('amount')

    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if user.wallet_balance < amount:
        raise HTTPException(status_code=400, detail="Insufficient funds")

    # Implement logic to withdraw funds from the wallet
    user.wallet_balance -= amount

    # Log the transaction securely
    try:
        transaction = WalletTransaction(
            user_id=user.id,
            amount=amount,
            transaction_type='withdrawal',
            date=datetime.now()
        )
        db.add(transaction)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed")

    return {"message": "Funds withdrawn from wallet successfully"}
