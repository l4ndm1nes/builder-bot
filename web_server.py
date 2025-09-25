#!/usr/bin/env python3
"""
Простой веб-сервер для health check и мониторинга
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import os
from datetime import datetime

app = FastAPI(title="Construction Bot API", version="1.0.0")

@app.get("/")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "service": "construction-bot",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@app.get("/status")
async def status():
    """Подробный статус системы"""
    try:
        from database import SessionLocal
        from google_sheets import sheets_manager
        
        # Проверяем базу данных
        db_status = "healthy"
        try:
            db = SessionLocal()
            db.close()
        except Exception as e:
            db_status = f"error: {str(e)}"
        
        # Проверяем Google Sheets
        sheets_status = "healthy" if sheets_manager.sheet else "error: not connected"
        
        return JSONResponse({
            "status": "healthy",
            "database": db_status,
            "google_sheets": sheets_status,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

@app.get("/metrics")
async def metrics():
    """Метрики для мониторинга"""
    try:
        from database import SessionLocal, User, Request
        
        db = SessionLocal()
        
        # Подсчитываем пользователей и заявки
        total_users = db.query(User).count()
        active_requests = db.query(Request).filter(Request.status == 'active').count()
        client_requests = db.query(Request).filter(
            Request.request_type == 'client',
            Request.status == 'active'
        ).count()
        contractor_requests = db.query(Request).filter(
            Request.request_type == 'contractor',
            Request.status == 'active'
        ).count()
        
        db.close()
        
        return JSONResponse({
            "total_users": total_users,
            "active_requests": active_requests,
            "client_requests": client_requests,
            "contractor_requests": contractor_requests,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }, status_code=500)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
