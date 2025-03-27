from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    google_refresh_token = Column(Text, nullable=False)
    bills = relationship("Bill", back_populates="user")

class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message_id = Column(String, index=True)
    vendor = Column(String, nullable=True)
    date = Column(String, nullable=True)
    due_date = Column(String, nullable=True)
    amount = Column(Numeric(12, 2), nullable=True)
    currency = Column(String(10), nullable=True)
    category = Column(String, nullable=True)
    status = Column(String, nullable=True)
    blob_name = Column(String, nullable=True)
    paid = Column(Boolean, default=False, nullable=False)
    
    user = relationship("User", back_populates="bills")
