from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./shopping_market.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# FastAPI app
app = FastAPI()

# SQLAlchemy model
class ShoppingItem(Base):
    __tablename__ = "shopping_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    quantity = Column(Integer, default=1)
    description = Column(String, nullable=True)

# Create tables
Base.metadata.create_all(bind=engine)

# Pydantic schemas
class ShoppingItemCreate(BaseModel):
    name: str
    quantity: int
    description: str | None = None

class ShoppingItemResponse(BaseModel):
    id: int
    name: str
    quantity: int
    description: str | None

    class Config:
        from_attributes = True  # For compatibility with SQLAlchemy models

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# CRUD operations
def get_shopping_item(db: Session, item_id: int):
    return db.query(ShoppingItem).filter(ShoppingItem.id == item_id).first()

def get_shopping_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(ShoppingItem).offset(skip).limit(limit).all()

def create_shopping_item(db: Session, item: ShoppingItemCreate):
    db_item = ShoppingItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

def update_shopping_item(db: Session, item_id: int, item: ShoppingItemCreate):
    db_item = db.query(ShoppingItem).filter(ShoppingItem.id == item_id).first()
    if db_item:
        db_item.name = item.name
        db_item.quantity = item.quantity
        db_item.description = item.description
        db.commit()
        db.refresh(db_item)
    return db_item

def delete_shopping_item(db: Session, item_id: int):
    db_item = db.query(ShoppingItem).filter(ShoppingItem.id == item_id).first()
    if db_item:
        db.delete(db_item)
        db.commit()
    return db_item

# FastAPI endpoints
@app.post("/items/", response_model=ShoppingItemResponse)
def create_item(item: ShoppingItemCreate, db: Session = Depends(get_db)):
    return create_shopping_item(db, item)

@app.get("/items/", response_model=list[ShoppingItemResponse])
def read_items(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = get_shopping_items(db, skip=skip, limit=limit)
    return items

@app.get("/items/{item_id}", response_model=ShoppingItemResponse)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = get_shopping_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.put("/items/{item_id}", response_model=ShoppingItemResponse)
def update_item(item_id: int, item: ShoppingItemCreate, db: Session = Depends(get_db)):
    db_item = update_shopping_item(db, item_id, item)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item

@app.delete("/items/{item_id}", response_model=ShoppingItemResponse)
def delete_item(item_id: int, db: Session = Depends(get_db)):
    db_item = delete_shopping_item(db, item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return db_item
