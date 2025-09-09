from flask import Flask, request, jsonify
from flask_cors import CORS
import schedule
import time
import threading
import logging
from datetime import datetime, timedelta
import os
import json
import requests
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/task_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# 任务存储
tasks = {}
task_results = {}
executor = ThreadPoolExecutor(max_workers=5)
scheduler_thread = None
scheduler_running = False

class TaskScheduler:
    def __init__(self):
        self.tasks = {}
        self.lock = threading.Lock()
    
    def add_task(self, task_id, task_config):
        """添加定时任务"""
        with self.lock:
            self.tasks[task_id] = {
                'config': task_config,
                'status': 'scheduled',
                'created_at': datetime.now().isoformat(),
                'last_run': None,
                'next_run': None,
                'run_count': 0
            }
        
        # 根据配置创建schedule任务
        self._schedule_task(task_id, task_config)
        logger.info(f"Task {task_id} scheduled")
    
    def _schedule_task(self, task_id, config):
        """创建schedule任务"""
        interval_type = config.get('interval_type', 'minutes')
        interval_value = config.get('interval_value', 5)
        
        if interval_type == 'seconds':
            schedule.every(interval_value).seconds.do(self._execute_task, task_id)
        elif interval_type == 'minutes':
            schedule.every(interval_value).minutes.do(self._execute_task, task_id)
        elif interval_type == 'hours':
            schedule.every(interval_value).hours.do(self._execute_task, task_id)
        elif interval_type == 'days':
            schedule.every(interval_value).days.do(self._execute_task, task_id)
    
    def _execute_task(self, task_id):
        """执行任务"""
        try:
            with self.lock:
                task = self.tasks.get(task_id)
            
            if not task:
                return
            
            config = task['config']
            
            # 更新任务状态
            with self.lock:
                self.tasks[task_id]['status'] = 'running'
                self.tasks[task_id]['last_run'] = datetime.now().isoformat()
                self.tasks[task_id]['run_count'] += 1
            
            # 执行任务
            result = self._call_service(config)
            
            # 保存结果
            task_results[f"{task_id}_{datetime.now().isoformat()}"] = result
            
            # 更新任务状态
            with self.lock:
                self.tasks[task_id]['status'] = 'completed'
            
            logger.info(f"Task {task_id} executed successfully")
            
        except Exception as e:
            logger.error(f"Task {task_id} execution failed: {str(e)}")
            with self.lock:
                self.tasks[task_id]['status'] = 'failed'
    
    def _call_service(self, config):
        """调用服务"""
        service_type = config.get('service_type')
        service_config = config.get('service_config', {})
        
        if service_type == 'ssh':
            return self._call_ssh_service(service_config)
        elif service_type == 'api':
            return self._call_api_service(service_config)
        elif service_type == 'snmp':
            return self._call_snmp_service(service_config)
        else:
            raise ValueError(f"Unknown service type: {service_type}")
    
    def _call_ssh_service(self, config):
        """调用SSH服务"""
        api_gateway_url = os.getenv('API_GATEWAY_URL', 'http://localhost:8000')
        
        # 建立连接
        connect_response = requests.post(
            f"{api_gateway_url}/api/ssh/connect",
            json=config.get('connection', {})
        )
        
        if connect_response.status_code != 200:
            raise Exception(f"SSH connection failed: {connect_response.text}")
        
        connection_id = connect_response.json()['connection_id']
        
        try:
            # 执行命令
            execute_response = requests.post(
                f"{api_gateway_url}/api/ssh/execute",
                json={
                    'connection_id': connection_id,
                    'command': config.get('command', 'echo "Hello World"')
                }
            )
            
            result = execute_response.json()
            
        finally:
            # 断开连接
            requests.post(
                f"{api_gateway_url}/api/ssh/disconnect",
                json={'connection_id': connection_id}
            )
        
        return result
    
    def _call_api_service(self, config):
        """调用API服务"""
        api_gateway_url = os.getenv('API_GATEWAY_URL', 'http://localhost:8000')
        
        response = requests.post(
            f"{api_gateway_url}/api/api/collect",
            json=config
        )
        
        return response.json()
    
    def _call_snmp_service(self, config):
        """调用SNMP服务"""
        api_gateway_url = os.getenv('API_GATEWAY_URL', 'http://localhost:8000')
        
        response = requests.post(
            f"{api_gateway_url}/api/snmp/collect",
            json=config
        )
        
        return response.json()
    
    def remove_task(self, task_id):
        """移除任务"""
        with self.lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                # 清除schedule中的任务
                schedule.clear(task_id)
                logger.info(f"Task {task_id} removed")
                return True
        return False
    
    def get_tasks(self):
        """获取所有任务"""
        with self.lock:
            return dict(self.tasks)

task_scheduler = TaskScheduler()

def run_scheduler():
    """运行调度器"""
    global scheduler_running
    scheduler_running = True
    
    while scheduler_running:
        schedule.run_pending()
        time.sleep(1)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'task-scheduler',
        'scheduler_running': scheduler_running,
        'active_tasks': len(task_scheduler.get_tasks())
    })

@app.route('/tasks', methods=['POST'])
def create_task():
    """创建定时任务"""
    data = request.get_json()
    
    if 'task_id' not in data or 'config' not in data:
        return jsonify({'error': 'Missing task_id or config'}), 400
    
    task_id = data['task_id']
    config = data['config']
    
    task_scheduler.add_task(task_id, config)
    
    return jsonify({
        'task_id': task_id,
        'status': 'scheduled',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/tasks', methods=['GET'])
def list_tasks():
    """列出所有任务"""
    tasks = task_scheduler.get_tasks()
    return jsonify({
        'tasks': tasks,
        'count': len(tasks),
        'timestamp': datetime.now().isoformat()
    })

@app.route('/tasks/<task_id>', methods=['DELETE'])
def delete_task(task_id):
    """删除任务"""
    success = task_scheduler.remove_task(task_id)
    
    if success:
        return jsonify({
            'status': 'deleted',
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({'error': 'Task not found'}), 404

@app.route('/results', methods=['GET'])
def get_results():
    """获取任务执行结果"""
    return jsonify({
        'results': task_results,
        'count': len(task_results),
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # 确保日志目录存在
    os.makedirs('logs', exist_ok=True)
    
    # 启动调度器线程
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    logger.info("Starting Task Scheduler...")
    app.run(host='0.0.0.0', port=8040, debug=False)