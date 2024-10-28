from typing import Optional
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import asc, create_engine, Column, Integer, String, Float, desc
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import psycopg2

# Create a FastAPI instance
app = FastAPI()     # This FastAPI instance is used to define routes, manages application lifecycle and handles API request.


# Database connection settings
DATABASE_URL = "postgresql://dhruvin:0000@localhost:3306/Temp"

# Set up the database enginer and session
engine = create_engine(DATABASE_URL)        # Connects Postgres database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)         # Manages database session 
Base = declarative_base()       # Used to define models(tables) in database which are class in python code to achieve ORM - Object Relationship Management

# Define a Product model 
class Product(Base):
    __tablename__ = "products"

    product_id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, index=True)
    product_price = Column(Float)
    description = Column(String)
    stock = Column(Integer)

# Create the database tables
Base.metadata.create_all(bind=engine)

# Pydantic model for request/response validation Automatically
class ProductCreate(BaseModel):
    product_name: str
    product_price: float
    description: str
    stock: int

# Pydantic model for Validation (Used for update)
class ProductUpdate(BaseModel):
    product_name : str
    product_price : float
    description : str
    stock : int

# Pydantic model for Partial Update
class ProductPartialUpdate(BaseModel):
    product_name : Optional [str] = None
    product_price : Optional [float] = None
    description : Optional [str] = None
    stock : Optional [int] = None

# Dependency function to create database session for each request and ensures that session is closed after handling request.
def get_db():
    db = SessionLocal()
    try:
        yield db        # This allows the session to be used during request and close it after the request is handled.
    finally:
        db.close()

# An endpoint to add products
@app.post("/products/")         # Endpoint to create product
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(product_name = product.product_name,product_price = product.product_price, description = product.description, stock = product.stock)
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# An endpoint to fetch all products
@app.get("/products/")          #Endpoint to get product
def read_products(skip: int= 0, limit: int = 10, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products


# An endpoint to update a product with PUT (Replace the full record)
@app.put("/products/{product_id}")
def update_product(product_id:int , updated_product: ProductUpdate, db: Session = Depends(get_db)):
    # Find the product by ID
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update the products's fields
    product.product_name = updated_product.product_name
    product.product_price = updated_product.product_price
    product.description = updated_product.description
    product.stock = updated_product.stock

    # Save the changes
    db.commit()
    db.refresh(product)

    return {"message": "Product updated successfully", "product":product}

# Update part of a product with PATCH (only update provided fields)
@app.patch("/products/{product_id}")
def update_product_partial(product_id: int, updated_product: ProductPartialUpdate, db: Session = Depends(get_db)):
    # Find the product by ID
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Update the product's fields selectively
    if updated_product.product_name is not None:
        product.product_name = updated_product.product_name

    if updated_product.product_price is not None:
        product.product_price = updated_product.product_price
    
    if updated_product.description is not None:
        product.description = updated_product.description
    
    if updated_product.stock is not None:
        product.stock = updated_product.stock

    # Save the changes
    db.commit()
    db.refresh(product)

    return {"message":"Product updated successfully", "product":product}

# Delete a record using Delete endpoint
@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    # Find the product by ID
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    # Delete the product
    db.delete(product)
    db.commit()

    return {"message": "Product deleted successfully"}

# Filtering and sorting in the GET Endpoint
@app.get("/filter/")
def read_products(category: Optional[str] = None, sort_by: Optional[str] = None, db: Session = Depends(get_db)):
    # Base query 
    product = db.query(Product)

    # Filter by catergory logic
    if category:
        product = product.filter(Product.description == category)


    # Sorting logic
    if sort_by == "price_asc":
        product = product.order_by(asc(Product.product_price))
    elif sort_by == "price_desc":
        product = product.order_by(desc(Product.product_price))

    products = product.all()
    if not products:
        raise HTTPException(status_code=500, detail="Category not found")
    return products