from flask import Flask, request, jsonify
from flask_cors import CORS
import paramiko
import logging
from datetime import datetime
import os
import json
from concurrent.futures import ThreadPoolExecutor
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ssh_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 线程池
executor = ThreadPoolExecutor(max_workers=10)

class SSHCollector:
    def __init__(self):
        self.active_connections = {}
        self.lock = threading.Lock()
    
    def connect(self, host, port, username, password, timeout=30):
        """建立SSH连接"""
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(
                hostname=host,
                port=port,
                username=username,
                password=password,
                timeout=timeout
            )
            
            connection_id = f"{host}:{port}:{username}"
            with self.lock:
                self.active_connections[connection_id] = client
            
            return connection_id, None
        except Exception as e:
            logger.error(f"SSH connection failed: {str(e)}")
            return None, str(e)
    
    def execute_command(self, connection_id, command):
        """执行SSH命令"""
        try:
            with self.lock:
                client = self.active_connections.get(connection_id)
            
            if not client:
                return None, "Connection not found"
            
            stdin, stdout, stderr = client.exec_command(command)
            
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            exit_status = stdout.channel.recv_exit_status()
            
            return {
                'output': output,
                'error': error,
                'exit_status': exit_status,
                'timestamp': datetime.now().isoformat()
            }, None
        except Exception as e:
            logger.error(f"Command execution failed: {str(e)}")
            return None, str(e)
    
    def disconnect(self, connection_id):
        """断开SSH连接"""
        try:
            with self.lock:
                client = self.active_connections.pop(connection_id, None)
            
            if client:
                client.close()
                return True
            return False
        except Exception as e:
            logger.error(f"Disconnect failed: {str(e)}")
            return False

ssh_collector = SSHCollector()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'ssh-collector',
        'active_connections': len(ssh_collector.active_connections)
    })

@app.route('/connect', methods=['POST'])
def connect():
    """建立SSH连接"""
    data = request.get_json()
    
    required_fields = ['host', 'port', 'username', 'password']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400
    
    connection_id, error = ssh_collector.connect(
        data['host'],
        data['port'],
        data['username'],
        data['password'],
        data.get('timeout', 30)
    )
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify({
        'connection_id': connection_id,
        'status': 'connected',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/execute', methods=['POST'])
def execute():
    """执行SSH命令"""
    data = request.get_json()
    
    if 'connection_id' not in data or 'command' not in data:
        return jsonify({'error': 'Missing connection_id or command'}), 400
    
    result, error = ssh_collector.execute_command(
        data['connection_id'],
        data['command']
    )
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify(result)

@app.route('/disconnect', methods=['POST'])
def disconnect():
    """断开SSH连接"""
    data = request.get_json()
    
    if 'connection_id' not in data:
        return jsonify({'error': 'Missing connection_id'}), 400
    
    success = ssh_collector.disconnect(data['connection_id'])
    
    if success:
        return jsonify({
            'status': 'disconnected',
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'Connection not found'}), 404

@app.route('/connections', methods=['GET'])
def list_connections():
    """列出活动连接"""
    with ssh_collector.lock:
        connections = list(ssh_collector.active_connections.keys())
    
    return jsonify({
        'active_connections': connections,
        'count': len(connections),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting SSH Collector...")
    app.run(host='0.0.0.0', port=8010, debug=False)