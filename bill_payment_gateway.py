from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, Boolean, DateTime, ForeignKey
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

class BillPayment(Base):
    __tablename__ = "bill_payments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payee = Column(String(120), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    is_recurring = Column(Boolean, default=False)
    payment_status = Column(String(20), default="pending")  # 'pending', 'completed', 'failed'
    date = Column(DateTime, nullable=False)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoint to Pay a Bill
@app.post("/bill/pay", response_model=dict)
async def pay_bill(data: dict, db: Session = Depends(get_db)):
    current_user_email = data.get('current_user_email')  # You can pass the user's email as part of the request data
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    payee = data.get('payee')
    amount = data.get('amount')
    due_date = data.get('due_date')
    is_recurring = data.get('is_recurring', False)

    if not payee or not amount or amount <= 0 or not due_date:
        raise HTTPException(status_code=400, detail="Invalid bill payment details")

    try:
        # Integrate with utility companies or service providers for bill payment
        # Securely transmit payment data and implement payment confirmation
        
        payment = BillPayment(
            user_id=user.id,
            payee=payee,
            amount=amount,
            due_date=due_date,
            is_recurring=is_recurring,
            date=datetime.now()
        )
        db.add(payment)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Bill payment failed")

    return {"message": "Bill payment completed successfully"}

# API Endpoint to Get Recurring Bills
@app.get("/bill/recurring", response_model=dict)
async def get_recurring_bills(current_user_email: str, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    recurring_bills = db.query(BillPayment).filter_by(user_id=user.id, is_recurring=True).all()
    bill_data = [{
        "payee": bill.payee,
        "amount": bill.amount,
        "due_date": bill.due_date
    } for bill in recurring_bills]

    return {"recurring_bills": bill_data}
