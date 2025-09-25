from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, User, Request, Match
from config import Config

# Создаем движок базы данных
engine = create_engine(Config.DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Создает все таблицы в базе данных"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Получает сессию базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_user(telegram_id, username=None, first_name=None, last_name=None):
    """Получает или создает пользователя"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()

def create_request(user_id, request_type, **kwargs):
    """Создает новую заявку"""
    db = SessionLocal()
    try:
        request = Request(
            user_id=user_id,
            request_type=request_type,
            **kwargs
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request
    finally:
        db.close()

def get_active_requests(request_type=None, location=None):
    """Получает активные заявки с фильтрами"""
    db = SessionLocal()
    try:
        query = db.query(Request).filter(Request.status == 'active')
        
        if request_type:
            query = query.filter(Request.request_type == request_type)
        
        if location:
            query = query.filter(Request.location.ilike(f'%{location}%'))
        
        return query.all()
    finally:
        db.close()

def find_matches(client_request):
    """Находит подходящие заявки исполнителей для клиентской заявки"""
    db = SessionLocal()
    try:
        # Ищем исполнителей в том же регионе
        contractor_requests = db.query(Request).filter(
            Request.request_type == 'contractor',
            Request.status == 'active',
            Request.location.ilike(f'%{client_request.location}%')
        ).all()
        
        matches = []
        for contractor_req in contractor_requests:
            # Простая логика сопоставления
            score = 0.5  # базовая оценка
            
            # Проверяем тип техники
            if client_request.equipment_type and contractor_req.available_equipment:
                if client_request.equipment_type.lower() in contractor_req.available_equipment.lower():
                    score += 0.3
            
            # Проверяем бюджет
            if client_request.budget and contractor_req.price_per_hour:
                estimated_cost = contractor_req.price_per_hour * 8  # 8 часов в день
                if client_request.budget >= estimated_cost:
                    score += 0.2
            
            if score > 0.6:  # минимальный порог совпадения
                matches.append((contractor_req, score))
        
        return sorted(matches, key=lambda x: x[1], reverse=True)
    finally:
        db.close()
