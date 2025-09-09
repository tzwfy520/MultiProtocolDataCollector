import redis
import json
import logging
from typing import Any, Optional
import os
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, redis_url=None):
        if redis_url:
            parsed = urlparse(redis_url)
            self.client = redis.Redis(
                host=parsed.hostname,
                port=parsed.port or 6379,
                db=int(parsed.path.lstrip('/')) if parsed.path else 0,
                decode_responses=True
            )
        else:
            self.client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=int(os.getenv('REDIS_DB', 0)),
                decode_responses=True
            )
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置键值对"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            return self.client.set(key, value, ex=ex)
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    def get(self, key: str) -> Any:
        """获取值"""
        try:
            value = self.client.get(key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """删除键"""
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    def lpush(self, key: str, *values) -> int:
        """向列表左侧推入值"""
        try:
            serialized_values = []
            for value in values:
                if isinstance(value, (dict, list)):
                    serialized_values.append(json.dumps(value))
                else:
                    serialized_values.append(str(value))
            return self.client.lpush(key, *serialized_values)
        except Exception as e:
            logger.error(f"Redis lpush error: {e}")
            return 0
    
    def rpop(self, key: str) -> Any:
        """从列表右侧弹出值"""
        try:
            value = self.client.rpop(key)
            if value is None:
                return None
            
            # 尝试解析JSON
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            logger.error(f"Redis rpop error: {e}")
            return None
    
    def llen(self, key: str) -> int:
        """获取列表长度"""
        try:
            return self.client.llen(key)
        except Exception as e:
            logger.error(f"Redis llen error: {e}")
            return 0
    
    def ping(self) -> bool:
        """测试连接"""
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"Redis ping error: {e}")
            return False