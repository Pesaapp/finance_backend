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

class Investment(Base):
    __tablename__ = "investments"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    investment_type = Column(String(50), nullable=False)
    symbol = Column(String(10), nullable=False)
    quantity = Column(Float, nullable=False)
    purchase_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, nullable=False)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoint to Get User Investments
@app.get("/investments", response_model=dict)
async def get_user_investments(current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Placeholder: Implement integration with investment data sources (stocks, cryptocurrencies, mutual funds)
    # Fetch user's investments and provide real-time market data
    
    investment_data = [{
        'investment_type': investment.investment_type,
        'symbol': investment.symbol,
        'quantity': investment.quantity,
        'purchase_price': investment.purchase_price,
        'purchase_date': investment.purchase_date
    } for investment in investments]

    return {"investments": investment_data}

# API Endpoint to Buy Investment
@app.post("/investments/buy", response_model=dict)
async def buy_investment(data: dict, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    investment_type = data.get('investment_type')
    symbol = data.get('symbol')
    quantity = data.get('quantity')
    purchase_price = data.get('purchase_price')

    if not investment_type or not symbol or not quantity or quantity <= 0 or not purchase_price or purchase_price <= 0:
        raise HTTPException(status_code=400, detail="Invalid investment details")

    # Placeholder: Implement integration with investment data sources (stocks, cryptocurrencies, mutual funds)
    # Implement logic to buy the investment, deduct funds, and record the transaction
    # Ensure proper error handling and validation
    
    try:
        investment = Investment(
            user_id=user.id,
            investment_type=investment_type,
            symbol=symbol,
            quantity=quantity,
            purchase_price=purchase_price,
            purchase_date=datetime.now()
        )
        db.add(investment)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Investment purchase failed")

    return {"message": "Investment purchased successfully"}

# API Endpoint to Sell Investment
@app.post("/investments/sell", response_model=dict)
async def sell_investment(data: dict, current_user_email: str = Depends(get_jwt_identity), db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=current_user_email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    symbol = data.get('symbol')
    quantity = data.get('quantity')
    selling_price = data.get('selling_price')

    if not symbol or not quantity or quantity <= 0 or not selling_price or selling_price <= 0:
        raise HTTPException(status_code=400, detail="Invalid sell details")

    # Placeholder: Implement integration with investment data sources (stocks, cryptocurrencies, mutual funds)
    # Implement logic to sell the investment, update funds, and record the transaction
    # Update investment quantity, calculate gains/losses, and record the transaction
    # Ensure proper error handling and validation
    
    try:
        # Implement logic to sell the investment and update the user's balance
        # Update investment quantity, calculate gains/losses, and record the transaction
        # Ensure proper error handling and validation
        
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Investment sale failed")

    return {"message": "Investment sold successfully"}
