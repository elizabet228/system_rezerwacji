from sqlalchemy import Column, Integer, String, DateTime, Enum, Boolean, ForeignKey
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    role = Column(Enum('employee', 'admin'), default='employee')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Room(Base):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    capacity = Column(Integer)
    location = Column(String(255))
    is_active = Column(Boolean, default=True)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    room_id = Column(Integer, ForeignKey("rooms.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    status = Column(Enum('confirmed', 'cancelled'), default='confirmed')