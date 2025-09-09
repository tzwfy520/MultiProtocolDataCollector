from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json

class ProtocolType(Enum):
    SSH = "ssh"
    API = "api"
    SNMP = "snmp"
    NETMIKO_SSH = "netmiko-ssh"
    GO_SSH = "go-ssh"

class ManagementType(Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"

class ServerStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"

class TaskType(Enum):
    COMMAND = "command"
    API_CALL = "api_call"
    SNMP_GET = "snmp_get"
    SNMP_WALK = "snmp_walk"

class TaskStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ResultStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class ConnectionStatus(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

@dataclass
class Server:
    """服务器模型"""
    id: Optional[int] = None
    name: str = ""
    host: str = ""
    port: int = 22
    username: str = ""
    password: str = ""
    protocol_type: ProtocolType = ProtocolType.SSH
    device_type: str = "linux"
    management_type: ManagementType = ManagementType.MANUAL
    status: ServerStatus = ServerStatus.ACTIVE
    description: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理枚举类型
        if isinstance(self.protocol_type, ProtocolType):
            data['protocol_type'] = self.protocol_type.value
        if isinstance(self.management_type, ManagementType):
            data['management_type'] = self.management_type.value
        if isinstance(self.status, ServerStatus):
            data['status'] = self.status.value
        # 处理日期时间
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        if self.updated_at:
            data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Server':
        """从字典创建实例"""
        # 处理枚举类型
        if 'protocol_type' in data and isinstance(data['protocol_type'], str):
            data['protocol_type'] = ProtocolType(data['protocol_type'])
        if 'management_type' in data and isinstance(data['management_type'], str):
            data['management_type'] = ManagementType(data['management_type'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = ServerStatus(data['status'])
        # 处理日期时间
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'updated_at' in data and isinstance(data['updated_at'], str):
            data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)

@dataclass
class CollectionTask:
    """数据采集任务模型"""
    id: Optional[int] = None
    name: str = ""
    server_id: int = 0
    task_type: TaskType = TaskType.COMMAND
    task_config: Dict[str, Any] = None
    schedule_config: Optional[Dict[str, Any]] = None
    status: TaskStatus = TaskStatus.ACTIVE
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None
    run_count: int = 0
    success_count: int = 0
    error_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.task_config is None:
            self.task_config = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理枚举类型
        if isinstance(self.task_type, TaskType):
            data['task_type'] = self.task_type.value
        if isinstance(self.status, TaskStatus):
            data['status'] = self.status.value
        # 处理JSON字段
        if self.task_config:
            data['task_config'] = json.dumps(self.task_config) if isinstance(self.task_config, dict) else self.task_config
        if self.schedule_config:
            data['schedule_config'] = json.dumps(self.schedule_config) if isinstance(self.schedule_config, dict) else self.schedule_config
        # 处理日期时间
        for field in ['last_run_at', 'next_run_at', 'created_at', 'updated_at']:
            if getattr(self, field):
                data[field] = getattr(self, field).isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionTask':
        """从字典创建实例"""
        # 处理枚举类型
        if 'task_type' in data and isinstance(data['task_type'], str):
            data['task_type'] = TaskType(data['task_type'])
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TaskStatus(data['status'])
        # 处理JSON字段
        if 'task_config' in data and isinstance(data['task_config'], str):
            data['task_config'] = json.loads(data['task_config'])
        if 'schedule_config' in data and isinstance(data['schedule_config'], str):
            data['schedule_config'] = json.loads(data['schedule_config'])
        # 处理日期时间
        for field in ['last_run_at', 'next_run_at', 'created_at', 'updated_at']:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)

@dataclass
class CollectionResult:
    """采集结果模型"""
    id: Optional[int] = None
    task_id: int = 0
    server_id: int = 0
    execution_id: str = ""
    status: ResultStatus = ResultStatus.SUCCESS
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None
    collected_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理枚举类型
        if isinstance(self.status, ResultStatus):
            data['status'] = self.status.value
        # 处理JSON字段
        if self.result_data:
            data['result_data'] = json.dumps(self.result_data) if isinstance(self.result_data, dict) else self.result_data
        # 处理日期时间
        if self.collected_at:
            data['collected_at'] = self.collected_at.isoformat()
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CollectionResult':
        """从字典创建实例"""
        # 处理枚举类型
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = ResultStatus(data['status'])
        # 处理JSON字段
        if 'result_data' in data and isinstance(data['result_data'], str):
            data['result_data'] = json.loads(data['result_data'])
        # 处理日期时间
        if 'collected_at' in data and isinstance(data['collected_at'], str):
            data['collected_at'] = datetime.fromisoformat(data['collected_at'])
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

@dataclass
class SystemLog:
    """系统日志模型"""
    id: Optional[int] = None
    level: LogLevel = LogLevel.INFO
    service: str = ""
    message: str = ""
    context: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理枚举类型
        if isinstance(self.level, LogLevel):
            data['level'] = self.level.value
        # 处理JSON字段
        if self.context:
            data['context'] = json.dumps(self.context) if isinstance(self.context, dict) else self.context
        # 处理日期时间
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SystemLog':
        """从字典创建实例"""
        # 处理枚举类型
        if 'level' in data and isinstance(data['level'], str):
            data['level'] = LogLevel(data['level'])
        # 处理JSON字段
        if 'context' in data and isinstance(data['context'], str):
            data['context'] = json.loads(data['context'])
        # 处理日期时间
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        return cls(**data)

@dataclass
class ConnectionSession:
    """连接会话模型"""
    id: Optional[int] = None
    session_id: str = ""
    server_id: int = 0
    protocol_type: str = ""
    status: ConnectionStatus = ConnectionStatus.CONNECTED
    connected_at: Optional[datetime] = None
    disconnected_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理枚举类型
        if isinstance(self.status, ConnectionStatus):
            data['status'] = self.status.value
        # 处理日期时间
        for field in ['connected_at', 'disconnected_at', 'last_activity_at']:
            if getattr(self, field):
                data[field] = getattr(self, field).isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConnectionSession':
        """从字典创建实例"""
        # 处理枚举类型
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = ConnectionStatus(data['status'])
        # 处理日期时间
        for field in ['connected_at', 'disconnected_at', 'last_activity_at']:
            if field in data and isinstance(data[field], str):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)

@dataclass
class PerformanceMetric:
    """性能指标模型"""
    id: Optional[int] = None
    service_name: str = ""
    metric_name: str = ""
    metric_value: float = 0.0
    metric_unit: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
    collected_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        # 处理JSON字段
        if self.tags:
            data['tags'] = json.dumps(self.tags) if isinstance(self.tags, dict) else self.tags
        # 处理日期时间
        if self.collected_at:
            data['collected_at'] = self.collected_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PerformanceMetric':
        """从字典创建实例"""
        # 处理JSON字段
        if 'tags' in data and isinstance(data['tags'], str):
            data['tags'] = json.loads(data['tags'])
        # 处理日期时间
        if 'collected_at' in data and isinstance(data['collected_at'], str):
            data['collected_at'] = datetime.fromisoformat(data['collected_at'])
        return cls(**data)