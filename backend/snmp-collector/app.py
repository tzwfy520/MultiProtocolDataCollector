from flask import Flask, request, jsonify
from flask_cors import CORS
from pysnmp.hlapi import *
import logging
from datetime import datetime
import os
from concurrent.futures import ThreadPoolExecutor
import threading

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/snmp_collector.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 线程池
executor = ThreadPoolExecutor(max_workers=10)

class SNMPCollector:
    def __init__(self):
        self.lock = threading.Lock()
    
    def get_snmp_data(self, host, community, oid, port=161, timeout=10):
        """获取SNMP数据"""
        try:
            iterator = getCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((host, port), timeout=timeout),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            )
            
            errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
            
            if errorIndication:
                return None, str(errorIndication)
            elif errorStatus:
                return None, f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}"
            else:
                result = []
                for varBind in varBinds:
                    oid_str = str(varBind[0])
                    value = str(varBind[1])
                    result.append({
                        'oid': oid_str,
                        'value': value
                    })
                
                return {
                    'host': host,
                    'community': community,
                    'data': result,
                    'timestamp': datetime.now().isoformat()
                }, None
                
        except Exception as e:
            logger.error(f"SNMP get failed: {str(e)}")
            return None, str(e)
    
    def walk_snmp_data(self, host, community, oid, port=161, timeout=10):
        """SNMP Walk操作"""
        try:
            result = []
            
            for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(),
                CommunityData(community),
                UdpTransportTarget((host, port), timeout=timeout),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False
            ):
                if errorIndication:
                    return None, str(errorIndication)
                elif errorStatus:
                    return None, f"{errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1][0] or '?'}"
                else:
                    for varBind in varBinds:
                        oid_str = str(varBind[0])
                        value = str(varBind[1])
                        result.append({
                            'oid': oid_str,
                            'value': value
                        })
            
            return {
                'host': host,
                'community': community,
                'data': result,
                'count': len(result),
                'timestamp': datetime.now().isoformat()
            }, None
            
        except Exception as e:
            logger.error(f"SNMP walk failed: {str(e)}")
            return None, str(e)
    
    def batch_collect(self, configs):
        """批量收集SNMP数据"""
        results = []
        
        for config in configs:
            operation = config.get('operation', 'get')
            
            if operation == 'get':
                result, error = self.get_snmp_data(
                    config['host'],
                    config['community'],
                    config['oid'],
                    config.get('port', 161),
                    config.get('timeout', 10)
                )
            elif operation == 'walk':
                result, error = self.walk_snmp_data(
                    config['host'],
                    config['community'],
                    config['oid'],
                    config.get('port', 161),
                    config.get('timeout', 10)
                )
            else:
                error = f"Unknown operation: {operation}"
                result = None
            
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

snmp_collector = SNMPCollector()

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'snmp-collector'
    })

@app.route('/get', methods=['POST'])
def snmp_get():
    """SNMP Get操作"""
    data = request.get_json()
    
    required_fields = ['host', 'community', 'oid']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields: host, community, oid'}), 400
    
    result, error = snmp_collector.get_snmp_data(
        data['host'],
        data['community'],
        data['oid'],
        data.get('port', 161),
        data.get('timeout', 10)
    )
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify(result)

@app.route('/walk', methods=['POST'])
def snmp_walk():
    """SNMP Walk操作"""
    data = request.get_json()
    
    required_fields = ['host', 'community', 'oid']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields: host, community, oid'}), 400
    
    result, error = snmp_collector.walk_snmp_data(
        data['host'],
        data['community'],
        data['oid'],
        data.get('port', 161),
        data.get('timeout', 10)
    )
    
    if error:
        return jsonify({'error': error}), 500
    
    return jsonify(result)

@app.route('/collect', methods=['POST'])
def collect():
    """通用收集接口"""
    data = request.get_json()
    
    operation = data.get('operation', 'get')
    
    if operation == 'get':
        return snmp_get()
    elif operation == 'walk':
        return snmp_walk()
    else:
        return jsonify({'error': f'Unknown operation: {operation}'}), 400

@app.route('/batch-collect', methods=['POST'])
def batch_collect():
    """批量收集SNMP数据"""
    data = request.get_json()
    
    if 'configs' not in data or not isinstance(data['configs'], list):
        return jsonify({'error': 'Missing or invalid configs array'}), 400
    
    results = snmp_collector.batch_collect(data['configs'])
    
    return jsonify({
        'results': results,
        'count': len(results),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/test-connection', methods=['POST'])
def test_connection():
    """测试SNMP连接"""
    data = request.get_json()
    
    required_fields = ['host', 'community']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields: host, community'}), 400
    
    # 使用系统OID测试连接
    test_oid = '1.3.6.1.2.1.1.1.0'  # sysDescr
    
    result, error = snmp_collector.get_snmp_data(
        data['host'],
        data['community'],
        test_oid,
        data.get('port', 161),
        data.get('timeout', 5)
    )
    
    if error:
        return jsonify({
            'connected': False,
            'error': error,
            'timestamp': datetime.now().isoformat()
        })
    
    return jsonify({
        'connected': True,
        'system_description': result['data'][0]['value'] if result['data'] else 'N/A',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    logger.info("Starting SNMP Collector...")
    app.run(host='0.0.0.0', port=8030, debug=False)