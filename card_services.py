from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
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
    has_virtual_card = Column(Boolean, default=False)
    card_activated = Column(Boolean, default=False)

class CardTransaction(Base):
    __tablename__ = "card_transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(String(20), nullable=False)  # 'purchase' or 'withdrawal'
    date = Column(DateTime, nullable=False)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoint to Activate a Card
@app.post("/card/activate", response_model=dict)
async def activate_card(data: dict, db: Session = Depends(get_db)):
    current_user_email = data.get('current_user_email')  # You can pass the user's email as part of the request data
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.has_virtual_card and not user.card_activated:
        # Integrate with the card service provider to activate the card
        # Implement tokenization and secure card activation process
        # Ensure compliance with PCI DSS and industry security standards
        
        # Simulate card activation
        user.card_activated = True
        db.commit()
        return {"message": "Card activated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Card activation failed")

# API Endpoint to Deactivate a Card
@app.post("/card/deactivate", response_model=dict)
async def deactivate_card(data: dict, db: Session = Depends(get_db)):
    current_user_email = data.get('current_user_email')  # You can pass the user's email as part of the request data
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.has_virtual_card and user.card_activated:
        # Integrate with the card service provider to deactivate the card
        # Implement secure deactivation process
        
        # Simulate card deactivation
        user.card_activated = False
        db.commit()
        return {"message": "Card deactivated successfully"}
    else:
        raise HTTPException(status_code=400, detail="Card deactivation failed")

# API Endpoint to Perform a Card Transaction
@app.post("/card/transaction", response_model=dict)
async def perform_card_transaction(data: dict, db: Session = Depends(get_db)):
    current_user_email = data.get('current_user_email')  # You can pass the user's email as part of the request data
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    amount = data.get('amount')
    transaction_type = data.get('transaction_type')

    if not amount or amount <= 0:
        raise HTTPException(status_code=400, detail="Invalid amount")

    if not user.has_virtual_card or not user.card_activated:
        raise HTTPException(status_code=400, detail="Card is not active")

    # Integrate with the card service provider to process the card transaction
    # Implement tokenization and secure card transaction handling
    # Implement fraud detection and prevention mechanisms
    
    try:
        transaction = CardTransaction(
            user_id=user.id,
            amount=amount,
            transaction_type=transaction_type,
            date=datetime.now()
        )
        db.add(transaction)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Transaction failed")

    return {"message": "Card transaction completed successfully"}
