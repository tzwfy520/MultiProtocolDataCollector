from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
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
        logging.FileHandler('logs/api_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 线程池
executor = ThreadPoolExecutor(max_workers=10)

class APICollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'MultiProtocol-DataCollector/1.0'
        })
    
    def collect_data(self, config):
        """收集API数据"""
        try:
            url = config.get('url')
            method = config.get('method', 'GET').upper()
            headers = config.get('headers', {})
            params = config.get('params', {})
            data = config.get('data', {})
            timeout = config.get('timeout', 30)
            
            # 更新请求头
            request_headers = self.session.headers.copy()
            request_headers.update(headers)
            
            # 发送请求
            if method == 'GET':
                response = self.session.get(
                    url, 
                    headers=request_headers,
                    params=params,
                    timeout=timeout
                )
            elif method == 'POST':
                response = self.session.post(
                    url,
                    headers=request_headers,
                    params=params,
                    json=data,
                    timeout=timeout
                )
            elif method == 'PUT':
                response = self.session.put(
                    url,
                    headers=request_headers,
                    params=params,
                    json=data,
                    timeout=timeout
                )
            elif method == 'DELETE':
                response = self.session.delete(
                    url,
                    headers=request_headers,
                    params=params,
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # 解析响应
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = response.text
            
            return {
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'data': response_data,
                'response_time': response.elapsed.total_seconds(),
                'timestamp': datetime.now().isoformat(),
                'success': response.status_code < 400
            }, None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None, str(e)
        except Exception as e:
            logger.error(f"API collection failed: {str(e)}")
            return None, str(e)
    
    def batch_collect(self, configs):
        """批量收集API数据"""
        results = []
        
        for config in configs:
            result, error = self.collect_data(config)
            if error:
                results.append({
                    'config': config,
                    'error': error,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                results.append({
                    'config': config,
                    'result': result,
                    'timestamp': datetime.now().isoformat()
                })
        
        return results

api_collector = APICollector()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'api-collector'
    })

@app.route('/collect', methods=['POST'])
def collect():
    """收集API数据"""
    data = request.get_json()
    
    if 'url' not in data:
        return jsonify({'error': 'Missing required field: url'}), 400
    
    result, error = api_collector.collect_data(data)
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify(result)

@app.route('/batch-collect', methods=['POST'])
def batch_collect():
    """批量收集API数据"""
    data = request.get_json()
    
    if 'configs' not in data or not isinstance(data['configs'], list):
        return jsonify({'error': 'Missing or invalid configs array'}), 400
    
    results = api_collector.batch_collect(data['configs'])
    
    return jsonify({
        'results': results,
        'count': len(results),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test-connection', methods=['POST'])
def test_connection():
    """测试API连接"""
    data = request.get_json()
    
    if 'url' not in data:
        return jsonify({'error': 'Missing required field: url'}), 400
    
    try:
        # 简单的连接测试
        test_config = {
            'url': data['url'],
            'method': 'GET',
            'timeout': 10
        }
        
        result, error = api_collector.collect_data(test_config)
        
        if error:
            return jsonify({
                'connected': False,
                'error': error,
                'timestamp': datetime.now().isoformat()
            })
        
        return jsonify({
            'connected': True,
            'status_code': result['status_code'],
            'response_time': result['response_time'],
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'connected': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting API Collector...")
    app.run(host='0.0.0.0', port=8020, debug=False)