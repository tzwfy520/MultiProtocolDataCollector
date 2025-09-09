from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import logging
from datetime import datetime
import os
from werkzeug.exceptions import RequestEntityTooLarge

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api_gateway.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# 服务注册表
SERVICES = {
    'ssh': 'http://localhost:8010',
    'api': 'http://localhost:8020', 
    'snmp': 'http://localhost:8030',
    'netmiko-ssh': 'http://localhost:8021',
    'go-ssh': 'http://localhost:8022',
    'task-scheduler': 'http://localhost:8040'
}

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({'error': 'File too large'}), 413

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'api-gateway'
    })

@app.route('/api/<service_name>/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def proxy_request(service_name, path):
    if service_name not in SERVICES:
        return jsonify({'error': f'Service {service_name} not found'}), 404
    
    service_url = SERVICES[service_name]
    target_url = f"{service_url}/{path}"
    
    try:
        # 转发请求
        if request.method == 'GET':
            response = requests.get(target_url, params=request.args, timeout=30)
        elif request.method == 'POST':
            response = requests.post(target_url, json=request.get_json(), timeout=30)
        elif request.method == 'PUT':
            response = requests.put(target_url, json=request.get_json(), timeout=30)
        elif request.method == 'DELETE':
            response = requests.delete(target_url, timeout=30)
        
        return jsonify(response.json()), response.status_code
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Error proxying request to {service_name}: {str(e)}")
        return jsonify({'error': f'Service {service_name} unavailable'}), 503

@app.route('/services', methods=['GET'])
def list_services():
    """列出所有可用服务"""
    service_status = {}
    
    for service_name, service_url in SERVICES.items():
        try:
            response = requests.get(f"{service_url}/health", timeout=5)
            service_status[service_name] = {
                'url': service_url,
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds()
            }
        except requests.exceptions.RequestException:
            service_status[service_name] = {
                'url': service_url,
                'status': 'unavailable',
                'response_time': None
            }
    
    return jsonify(service_status)

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting API Gateway...")
    app.run(host='0.0.0.0', port=8000, debug=False)