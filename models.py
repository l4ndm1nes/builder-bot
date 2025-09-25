from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    phone = Column(String(20))
    is_contractor = Column(Boolean, default=False)  # True - исполнитель, False - клиент
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

class Request(Base):
    __tablename__ = 'requests'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    request_type = Column(String(50), nullable=False)  # 'client' или 'contractor'
    
    # Основная информация
    title = Column(String(255), nullable=False)
    description = Column(Text)
    location = Column(String(255), nullable=False)
    
    # Для клиентов
    equipment_type = Column(String(100))  # экскаватор, кран, бульдозер и т.д.
    work_duration = Column(String(50))  # количество дней/часов
    budget = Column(Float)  # бюджет в гривнах
    
    # Для исполнителей
    available_equipment = Column(Text)  # список доступной техники
    experience_years = Column(Integer)
    price_per_hour = Column(Float)
    
    # Статус
    status = Column(String(50), default='active')  # active, matched, completed, cancelled
    matched_with = Column(Integer)  # ID сопоставленной заявки
    
    # Метаданные
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    expires_at = Column(DateTime)

class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    client_request_id = Column(Integer, nullable=False)
    contractor_request_id = Column(Integer, nullable=False)
    match_score = Column(Float)  # оценка совпадения 0-1
    status = Column(String(50), default='pending')  # pending, accepted, rejected, completed
    created_at = Column(DateTime, default=func.now())
    notes = Column(Text)  # заметки диспетчера
