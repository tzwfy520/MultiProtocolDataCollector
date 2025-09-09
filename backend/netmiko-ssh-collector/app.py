from flask import Flask, request, jsonify
from flask_cors import CORS
from netmiko import ConnectHandler, NetmikoTimeoutException, NetmikoAuthenticationException
import logging
from datetime import datetime
import os
import threading
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/netmiko_ssh_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 线程池
executor = ThreadPoolExecutor(max_workers=10)

class NetmikoSSHCollector:
    def __init__(self):
        self.active_connections = {}
        self.lock = threading.Lock()
    
    def connect(self, device_config):
        """建立Netmiko SSH连接"""
        try:
            # 设备配置
            device = {
                'device_type': device_config.get('device_type', 'cisco_ios'),
                'host': device_config['host'],
                'port': device_config.get('port', 22),
                'username': device_config['username'],
                'password': device_config['password'],
                'timeout': device_config.get('timeout', 30),
                'session_timeout': device_config.get('session_timeout', 60),
                'banner_timeout': device_config.get('banner_timeout', 15),
                'conn_timeout': device_config.get('conn_timeout', 10)
            }
            
            # 可选参数
            if 'secret' in device_config:
                device['secret'] = device_config['secret']
            if 'global_delay_factor' in device_config:
                device['global_delay_factor'] = device_config['global_delay_factor']
            
            connection = ConnectHandler(**device)
            
            connection_id = f"{device['host']}:{device['port']}:{device['username']}:{device['device_type']}"
            
            with self.lock:
                self.active_connections[connection_id] = {
                    'connection': connection,
                    'device_config': device_config,
                    'created_at': datetime.now().isoformat()
                }
            
            return connection_id, None
            
        except NetmikoTimeoutException as e:
            logger.error(f"Netmiko timeout: {str(e)}")
            return None, f"Connection timeout: {str(e)}"
        except NetmikoAuthenticationException as e:
            logger.error(f"Netmiko authentication failed: {str(e)}")
            return None, f"Authentication failed: {str(e)}"
        except Exception as e:
            logger.error(f"Netmiko connection failed: {str(e)}")
            return None, str(e)
    
    def execute_command(self, connection_id, command, use_textfsm=False):
        """执行命令"""
        try:
            with self.lock:
                conn_info = self.active_connections.get(connection_id)
            
            if not conn_info:
                return None, "Connection not found"
            
            connection = conn_info['connection']
            
            # 执行命令
            if use_textfsm:
                output = connection.send_command(command, use_textfsm=True)
            else:
                output = connection.send_command(command)
            
            return {
                'command': command,
                'output': output,
                'use_textfsm': use_textfsm,
                'timestamp': datetime.now().isoformat()
            }, None
            
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return None, str(e)
    
    def execute_config_commands(self, connection_id, commands, exit_config_mode=True):
        """执行配置命令"""
        try:
            with self.lock:
                conn_info = self.active_connections.get(connection_id)
            
            if not conn_info:
                return None, "Connection not found"
            
            connection = conn_info['connection']
            
            # 执行配置命令
            output = connection.send_config_set(
                commands, 
                exit_config_mode=exit_config_mode
            )
            
            return {
                'commands': commands,
                'output': output,
                'exit_config_mode': exit_config_mode,
                'timestamp': datetime.now().isoformat()
            }, None
            
        except Exception as e:
            logger.error(f"Config command execution failed: {str(e)}")
            return None, str(e)
    
    def disconnect(self, connection_id):
        """断开连接"""
        try:
            with self.lock:
                conn_info = self.active_connections.pop(connection_id, None)
            
            if conn_info:
                connection = conn_info['connection']
                connection.disconnect()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Disconnect failed: {str(e)}")
            return False
    
    def get_device_info(self, connection_id):
        """获取设备信息"""
        try:
            with self.lock:
                conn_info = self.active_connections.get(connection_id)
            
            if not conn_info:
                return None, "Connection not found"
            
            connection = conn_info['connection']
            
            # 获取基本信息
            info = {
                'device_type': connection.device_type,
                'host': connection.host,
                'port': connection.port,
                'username': connection.username,
                'is_alive': connection.is_alive(),
                'base_prompt': connection.base_prompt,
                'created_at': conn_info['created_at'],
                'timestamp': datetime.now().isoformat()
            }
            
            return info, None
            
        except Exception as e:
            logger.error(f"Get device info failed: {str(e)}")
            return None, str(e)

netmiko_collector = NetmikoSSHCollector()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'netmiko-ssh-collector',
        'active_connections': len(netmiko_collector.active_connections)
    })

@app.route('/connect', methods=['POST'])
def connect():
    """建立Netmiko SSH连接"""
    data = request.get_json()
    
    required_fields = ['host', 'username', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields: host, username, password'}), 400
    
    connection_id, error = netmiko_collector.connect(data)
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({
        'connection_id': connection_id,
        'status': 'connected',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/execute', methods=['POST'])
def execute():
    """执行命令"""
    data = request.get_json()
    
    if 'connection_id' not in data or 'command' not in data:
        return jsonify({'error': 'Missing connection_id or command'}), 400
    
    result, error = netmiko_collector.execute_command(
        data['connection_id'],
        data['command'],
        data.get('use_textfsm', False)
    )
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify(result)

@app.route('/config', methods=['POST'])
def config():
    """执行配置命令"""
    data = request.get_json()
    
    if 'connection_id' not in data or 'commands' not in data:
        return jsonify({'error': 'Missing connection_id or commands'}), 400
    
    result, error = netmiko_collector.execute_config_commands(
        data['connection_id'],
        data['commands'],
        data.get('exit_config_mode', True)
    )
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify(result)

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """断开连接"""
    data = request.get_json()
    
    if 'connection_id' not in data:
        return jsonify({'error': 'Missing connection_id'}), 400
    
    success = netmiko_collector.disconnect(data['connection_id'])
    
    if success:
        return jsonify({
            'status': 'disconnected',
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'Connection not found'}), 404

@app.route('/device-info', methods=['POST'])
def device_info():
    """获取设备信息"""
    data = request.get_json()
    
    if 'connection_id' not in data:
        return jsonify({'error': 'Missing connection_id'}), 400
    
    info, error = netmiko_collector.get_device_info(data['connection_id'])
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify(info)

@app.route('/connections', methods=['GET'])
def list_connections():
    """列出活动连接"""
    with netmiko_collector.lock:
        connections = {}
        for conn_id, conn_info in netmiko_collector.active_connections.items():
            connections[conn_id] = {
                'device_type': conn_info['device_config'].get('device_type', 'cisco_ios'),
                'host': conn_info['device_config']['host'],
                'port': conn_info['device_config'].get('port', 22),
                'username': conn_info['device_config']['username'],
                'created_at': conn_info['created_at']
            }
    
    return jsonify({
        'active_connections': connections,
        'count': len(connections),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting Netmiko SSH Collector...")
    app.run(host='0.0.0.0', port=8021, debug=False)