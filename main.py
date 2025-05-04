from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from io import BytesIO
import base64
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, History
from analyze_test_data import DataAnalyzer
from visual_test_data import Visualiser
import uvicorn

# Создаем экземпляр FastAPI c метаданными
app = FastAPI(
    title = "Wikipedia Article API",
    description = "API для доступа к статье и статистике просмотров",
    version = "1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Настройка подключения к SQLite
SQLALCHEMY_DATABASE_URL = "sqlite:///./wiki_history.db"

# Создаем "движок" для работы с БД
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}, # Нужно для SQLite в многопоточном режиме
    echo=True
)

# Создаем фабрику сессий для взаимодействия с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Создаем таблицы в БД, если они еще не созданы
Base.metadata.create_all(bind=engine)

# Зависимость для получения сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db # Возвращаем сессию для использования в эндпоинтах
    finally:
        db.close()

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")
        
# Эндпоинт для получения списка статей
@app.get('/wiki_history/')
def get_articles(
    skip: int = Query(0, description="Пагинация"),
    limit: int = Query(5, le=5, description="Лимит на выдачу (максимум 5)"),
    title: str = Query(None, description="Фильтр по заголовку"),
    sort_by: str = Query("id", enum=["id", "timestamp", "total_views", "average_daily_views"], description="Поле для сортировки"),
    order: str = Query("asc", enum=["asc", "desc"], description="Порядок сортировки"),
    db: Session = Depends(get_db) # Инъекция сессии БД
):
    # Проверка корректности параметров сортировки
    if sort_by not in ["id", "timestamp", "total_views", "average_daily_views"]:
        raise HTTPException(status_code=400, detail="Недопустимое поле для сортировки")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Недопустимый порядок для сортировки")
    
    # Формируем базовый запрос к БД
    query = db.query(History)
    
    # Применяем фильтр по заголовку
    if title:
        query = query.filter(History.title.contains(title))
        
    # Определяем направление сортировки
    order_column = getattr(History, sort_by)
    if order == "desc":
        order_column = order_column.desc()
        
    # Применяем сортировку и пагинацию
    articles = query.order_by(order_column).offset(skip).limit(limit).all()
    return articles

@app.get("/stats/")
def get_stats(db=Depends(get_db)):
    """Возвращает базовую статистику"""
    analyzer = DataAnalyzer("wiki_history.db")
    df = analyzer.load_data()
    if df.empty:
        return {"error": "Нет данных для анализа"}
    basic_stats = analyzer.get_basic_stats(df)
    
    # Добавим min/max просмотров
    min_entry = db.query(History).order_by(History.total_views).first()
    max_entry = db.query(History).order_by(History.total_views.desc()).first()
    
    return {
        "basic_stats": basic_stats,
        "min_views_entry": {
            "id": int(min_entry.id),
            "title": str(min_entry.title),
            "views": int(min_entry.total_views)
        },
        "max_views_entry": {
            "id": int(max_entry.id),
            "title": str(max_entry.title),
            "views": int(max_entry.total_views)
        }
    }
    
@app.get("/plots/content/evolution")
def get_content_evolution_plot():
    """Генерирует график эволюции контента"""
    analyzer = DataAnalyzer("wiki_history.db")
    df = analyzer.load_data()
    visualiser = Visualiser()
    fig = visualiser.plot_content_evolution(df)
    
    # Конвертируем в base64
    buf = BytesIO()
    fig.savefig(buf, format = "png")
    buf.seek(0)
    return HTMLResponse(content=f"<img src='data:image/png;base64, {base64.b64encode(buf.read()).decode()}' />")

@app.get("/plots/views")
def get_views_plot():
    """Генерирует графики просмотров"""
    analyzer = DataAnalyzer("wiki_history.db")
    df = analyzer.load_data()
    daily_stats = analyzer.get_daily_stats(df)
    
    visualiser = Visualiser()
    fig = visualiser.plot_views(daily_stats)
    
    buf = BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    return HTMLResponse(content=f"<img src='data:image/png;base64, {base64.b64encode(buf.read()).decode()}' />")
    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    

        
        
    
        