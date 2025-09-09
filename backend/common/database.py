import mysql.connector
from mysql.connector import Error
import logging
from contextlib import contextmanager
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url=None):
        if database_url:
            parsed = urlparse(database_url)
            self.config = {
                'host': parsed.hostname,
                'port': parsed.port or 3306,
                'user': parsed.username,
                'password': parsed.password,
                'database': parsed.path.lstrip('/'),
                'charset': 'utf8mb4',
                'autocommit': True
            }
        else:
            self.config = {
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': int(os.getenv('DB_PORT', 3306)),
                'user': os.getenv('DB_USER', 'multiproto'),
                'password': os.getenv('DB_PASSWORD', 'multiproto123'),
                'database': os.getenv('DB_NAME', 'multiproto_gather'),
                'charset': 'utf8mb4',
                'autocommit': True
            }
    
    @contextmanager
    def get_connection(self):
        connection = None
        try:
            connection = mysql.connector.connect(**self.config)
            yield connection
        except Error as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    def execute_query(self, query, params=None):
        """执行查询并返回结果"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        """执行更新操作"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.rowcount
    
    def execute_insert(self, query, params=None):
        """执行插入操作并返回插入的ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params or ())
            conn.commit()
            return cursor.lastrowid
    
    def test_connection(self):
        """测试数据库连接"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False