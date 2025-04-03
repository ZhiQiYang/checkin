"""
基礎數據模型，包括數據庫連接和模型基類
"""

import os
import sqlite3
import logging

class Database:
    """數據庫連接管理類"""
    
    DB_PATH = os.environ.get('DATABASE_PATH', 'checkin.db')
    
    @staticmethod
    def get_connection():
        """獲取數據庫連接"""
        try:
            return sqlite3.connect(Database.DB_PATH)
        except sqlite3.Error as e:
            logging.error(f"數據庫連接失敗: {e}")
            raise

    @staticmethod
    def execute_query(query, params=None, fetch_type=None):
        """
        執行SQL查詢並返回結果
        
        Parameters:
            query (str): SQL查詢語句
            params (tuple, dict, optional): 查詢參數
            fetch_type (str, optional): 結果獲取類型 ('one', 'all', None)
        
        Returns:
            結果, 或在INSERT操作時返回last_row_id
        """
        conn = None
        try:
            conn = Database.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            if query.strip().upper().startswith("SELECT"):
                if fetch_type == 'one':
                    result = cursor.fetchone()
                elif fetch_type == 'all':
                    result = cursor.fetchall()
                else:
                    result = None
            else:
                conn.commit()
                if query.strip().upper().startswith("INSERT"):
                    result = cursor.lastrowid
                else:
                    result = cursor.rowcount
                    
            return result
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            logging.error(f"數據庫查詢失敗: {query}, 錯誤: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @staticmethod
    def table_exists(table_name):
        """檢查表是否存在"""
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?"
        result = Database.execute_query(query, (table_name,), 'one')
        return result is not None
        
    @staticmethod
    def create_table(table_name, columns_definition):
        """創建表"""
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_definition})"
        Database.execute_query(query)

class Model:
    """所有模型的基類"""
    
    table_name = None
    columns = {}
    primary_key = "id"
    
    @classmethod
    def create_table_if_not_exists(cls):
        """如果表不存在，則創建表"""
        if cls.table_name and cls.columns:
            if not Database.table_exists(cls.table_name):
                columns_def = ", ".join([f"{col} {datatype}" for col, datatype in cls.columns.items()])
                Database.create_table(cls.table_name, columns_def)
                logging.info(f"創建表 {cls.table_name}")
    
    @classmethod
    def find_by_id(cls, id_value):
        """通過主鍵查找記錄"""
        query = f"SELECT * FROM {cls.table_name} WHERE {cls.primary_key} = ?"
        result = Database.execute_query(query, (id_value,), 'one')
        return result
    
    @classmethod
    def find_all(cls, conditions=None, params=None, order_by=None, limit=None):
        """查找多條記錄"""
        query = f"SELECT * FROM {cls.table_name}"
        
        if conditions:
            query += f" WHERE {conditions}"
            
        if order_by:
            query += f" ORDER BY {order_by}"
            
        if limit:
            query += f" LIMIT {limit}"
            
        return Database.execute_query(query, params, 'all')
    
    @classmethod
    def insert(cls, data):
        """插入新記錄"""
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        
        query = f"INSERT INTO {cls.table_name} ({columns}) VALUES ({placeholders})"
        return Database.execute_query(query, tuple(data.values()))
    
    @classmethod
    def update(cls, id_value, data):
        """更新記錄"""
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        
        query = f"UPDATE {cls.table_name} SET {set_clause} WHERE {cls.primary_key} = ?"
        
        params = list(data.values())
        params.append(id_value)
        
        return Database.execute_query(query, tuple(params))
    
    @classmethod
    def delete(cls, id_value):
        """刪除記錄"""
        query = f"DELETE FROM {cls.table_name} WHERE {cls.primary_key} = ?"
        return Database.execute_query(query, (id_value,))
        
    @classmethod
    def count(cls, conditions=None, params=None):
        """計算記錄數量"""
        query = f"SELECT COUNT(*) FROM {cls.table_name}"
        
        if conditions:
            query += f" WHERE {conditions}"
            
        result = Database.execute_query(query, params, 'one')
        return result[0] if result else 0 