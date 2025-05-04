from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

# Создаем базовый класс для моделей
Base = declarative_base()

# Определяем модель таблицы
class History(Base):
    __tablename__ = "wiki_history"
    
    # Колонки таблицы
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    char_count = Column(Integer)
    content = Column(Text)
    last_edit = Column(String(100))
    editor = Column(String(100))
    links = Column(Text)
    timestamp = Column(DateTime)
    diff = Column(Text)
    total_views = Column(Integer)
    average_daily_views = Column(Integer)
    
    