-- 多协议数据采集系统数据库初始化脚本

CREATE DATABASE IF NOT EXISTS multiproto_gather CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE multiproto_gather;

-- 服务器管理表
CREATE TABLE IF NOT EXISTS servers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '服务器名称',
    host VARCHAR(255) NOT NULL COMMENT '服务器地址',
    port INT NOT NULL DEFAULT 22 COMMENT '端口号',
    username VARCHAR(255) NOT NULL COMMENT '用户名',
    password VARCHAR(255) NOT NULL COMMENT '密码',
    protocol_type ENUM('ssh', 'api', 'snmp', 'netmiko-ssh', 'go-ssh') NOT NULL DEFAULT 'ssh' COMMENT '协议类型',
    device_type VARCHAR(100) DEFAULT 'linux' COMMENT '设备类型',
    management_type ENUM('manual', 'scheduled') NOT NULL DEFAULT 'manual' COMMENT '管理类型',
    status ENUM('active', 'inactive', 'error') NOT NULL DEFAULT 'active' COMMENT '状态',
    description TEXT COMMENT '描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_host_port (host, port),
    INDEX idx_protocol_type (protocol_type),
    INDEX idx_status (status),
    INDEX idx_management_type (management_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='服务器管理表';

-- 数据采集任务表
CREATE TABLE IF NOT EXISTS collection_tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL COMMENT '任务名称',
    server_id INT NOT NULL COMMENT '服务器ID',
    task_type ENUM('command', 'api_call', 'snmp_get', 'snmp_walk') NOT NULL COMMENT '任务类型',
    task_config JSON NOT NULL COMMENT '任务配置',
    schedule_config JSON COMMENT '调度配置',
    status ENUM('active', 'inactive', 'running', 'completed', 'failed') NOT NULL DEFAULT 'active' COMMENT '状态',
    last_run_at TIMESTAMP NULL COMMENT '最后运行时间',
    next_run_at TIMESTAMP NULL COMMENT '下次运行时间',
    run_count INT DEFAULT 0 COMMENT '运行次数',
    success_count INT DEFAULT 0 COMMENT '成功次数',
    error_count INT DEFAULT 0 COMMENT '错误次数',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    INDEX idx_server_id (server_id),
    INDEX idx_task_type (task_type),
    INDEX idx_status (status),
    INDEX idx_next_run_at (next_run_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='数据采集任务表';

-- 采集结果表
CREATE TABLE IF NOT EXISTS collection_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL COMMENT '任务ID',
    server_id INT NOT NULL COMMENT '服务器ID',
    execution_id VARCHAR(255) NOT NULL COMMENT '执行ID',
    status ENUM('success', 'failed', 'timeout') NOT NULL COMMENT '执行状态',
    result_data JSON COMMENT '结果数据',
    error_message TEXT COMMENT '错误信息',
    execution_time DECIMAL(10,3) COMMENT '执行时间(秒)',
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (task_id) REFERENCES collection_tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    INDEX idx_task_id (task_id),
    INDEX idx_server_id (server_id),
    INDEX idx_execution_id (execution_id),
    INDEX idx_status (status),
    INDEX idx_collected_at (collected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采集结果表';

-- 系统日志表
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level ENUM('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL') NOT NULL COMMENT '日志级别',
    service VARCHAR(100) NOT NULL COMMENT '服务名称',
    message TEXT NOT NULL COMMENT '日志消息',
    context JSON COMMENT '上下文信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    INDEX idx_level (level),
    INDEX idx_service (service),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统日志表';

-- 连接会话表
CREATE TABLE IF NOT EXISTS connection_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE COMMENT '会话ID',
    server_id INT NOT NULL COMMENT '服务器ID',
    protocol_type VARCHAR(50) NOT NULL COMMENT '协议类型',
    status ENUM('connected', 'disconnected', 'error') NOT NULL DEFAULT 'connected' COMMENT '连接状态',
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '连接时间',
    disconnected_at TIMESTAMP NULL COMMENT '断开时间',
    last_activity_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后活动时间',
    error_message TEXT COMMENT '错误信息',
    FOREIGN KEY (server_id) REFERENCES servers(id) ON DELETE CASCADE,
    INDEX idx_session_id (session_id),
    INDEX idx_server_id (server_id),
    INDEX idx_status (status),
    INDEX idx_connected_at (connected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='连接会话表';

-- 性能监控表
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL COMMENT '服务名称',
    metric_name VARCHAR(100) NOT NULL COMMENT '指标名称',
    metric_value DECIMAL(15,6) NOT NULL COMMENT '指标值',
    metric_unit VARCHAR(20) COMMENT '指标单位',
    tags JSON COMMENT '标签',
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
    INDEX idx_service_metric (service_name, metric_name),
    INDEX idx_collected_at (collected_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='性能监控表';

-- 插入初始数据
INSERT INTO servers (name, host, port, username, password, protocol_type, device_type, management_type, description) VALUES
('测试服务器', '192.168.1.100', 22, 'admin', 'testpass123', 'ssh', 'linux', 'manual', '用于测试的Linux服务器'),
('网络设备1', '192.168.1.1', 22, 'cisco', 'cisco123', 'netmiko-ssh', 'cisco_ios', 'scheduled', 'Cisco路由器'),
('API服务器', '192.168.1.200', 80, 'api_user', 'api_pass', 'api', 'api', 'manual', 'REST API服务器'),
('SNMP设备', '192.168.1.50', 161, 'public', '', 'snmp', 'snmp', 'scheduled', 'SNMP监控设备');

-- 插入示例任务
INSERT INTO collection_tasks (name, server_id, task_type, task_config, schedule_config, status) VALUES
('系统信息采集', 1, 'command', '{"command": "uname -a && df -h && free -m"}', '{"interval_type": "minutes", "interval_value": 5}', 'active'),
('网络接口状态', 2, 'command', '{"command": "show interfaces status"}', '{"interval_type": "minutes", "interval_value": 10}', 'active'),
('API健康检查', 3, 'api_call', '{"url": "http://192.168.1.200/health", "method": "GET"}', '{"interval_type": "minutes", "interval_value": 2}', 'active'),
('SNMP系统信息', 4, 'snmp_get', '{"oid": "1.3.6.1.2.1.1.1.0", "community": "public"}', '{"interval_type": "minutes", "interval_value": 15}', 'active');

-- 创建视图：服务器状态概览
CREATE OR REPLACE VIEW server_status_overview AS
SELECT 
    s.id,
    s.name,
    s.host,
    s.port,
    s.protocol_type,
    s.device_type,
    s.management_type,
    s.status,
    COUNT(ct.id) as task_count,
    COUNT(CASE WHEN ct.status = 'active' THEN 1 END) as active_tasks,
    MAX(cr.collected_at) as last_collection,
    s.created_at,
    s.updated_at
FROM servers s
LEFT JOIN collection_tasks ct ON s.id = ct.server_id
LEFT JOIN collection_results cr ON s.id = cr.server_id AND cr.status = 'success'
GROUP BY s.id, s.name, s.host, s.port, s.protocol_type, s.device_type, s.management_type, s.status, s.created_at, s.updated_at;

-- 创建视图：任务执行统计
CREATE OR REPLACE VIEW task_execution_stats AS
SELECT 
    ct.id,
    ct.name,
    ct.task_type,
    ct.status,
    ct.run_count,
    ct.success_count,
    ct.error_count,
    CASE 
        WHEN ct.run_count > 0 THEN ROUND((ct.success_count / ct.run_count) * 100, 2)
        ELSE 0
    END as success_rate,
    ct.last_run_at,
    ct.next_run_at,
    s.name as server_name,
    s.host as server_host
FROM collection_tasks ct
JOIN servers s ON ct.server_id = s.id;

COMMIT;