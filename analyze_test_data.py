import sqlite3
import pandas as pd
import json

class DataAnalyzer:
    def __init__(self, db_path="wiki_history.db"):
        self.db_path = db_path
        
    def load_data(self):
        """Загрузка и предобработка данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = "SELECT * FROM wiki_history"
                df = pd.read_sql(query, conn)
        except Exception as e:
            raise ValueError(f"Ошибка загрузки данных: {str(e)}")
            
            
        # Обработка JSON полей
        df['links'] = df['links'].apply(json.loads)
        df['diff'] = df['diff'].apply(json.loads)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def get_basic_stats(self, df):
        """Основная статистика"""
        return {
            'total_entries': int(len(df)),
            'average_char_count': int(df['char_count'].mean()),
            'total_views': int(df['total_views'].max()),
            'last_update': df['timestamp'].max().strftime('%Y-%m-%d')  
        }
        
    def get_daily_stats(self, df):
        """Статистика по дням"""
        daily = df.set_index('timestamp').resample("D").agg({
            'char_count': 'last',
            'total_views': 'last',
            'average_daily_views': 'mean'
        })
        
        return daily
    

    