# MultiProtocolDataCollector

一个企业级多协议数据采集系统，支持SSH、API、SNMP等多种协议的统一数据采集和管理。

## 🚀 特性

- **多协议支持**: SSH、HTTP/HTTPS API、SNMP v1/v2c/v3
- **微服务架构**: 基于Docker的微服务架构，易于扩展和维护
- **智能调度**: 支持亲和性和排斥性的任务调度策略
- **实时监控**: 完整的任务执行监控和系统状态监控
- **Web管理界面**: 直观易用的Web管理界面
- **高可用性**: 支持集群部署和负载均衡
- **数据安全**: 支持加密传输和访问控制

## 📋 系统要求

### 硬件要求
- **CPU**: 2核心以上
- **内存**: 4GB以上
- **磁盘**: 20GB以上可用空间
- **网络**: 稳定的网络连接

### 软件要求
- **操作系统**: Linux (推荐 Ubuntu 20.04+, CentOS 8+)
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Git**: 2.0+

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │ Task Scheduler  │
│   (Nginx)       │◄──►│   (Flask)       │◄──►│   (Flask)       │
│   Port: 80      │    │   Port: 8000    │    │   Port: 8040    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  SSH Collector  │    │  API Collector  │    │ SNMP Collector  │
│   Port: 8010    │    │   Port: 8020    │    │   Port: 8030    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐
│ Netmiko SSH     │    │   Go SSH        │
│ Collector       │    │   Collector     │
│ Port: 8021      │    │   Port: 8022    │
└─────────────────┘    └─────────────────┘
```

## 🚀 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/tzwfy520/MultiProtocolDataCollector.git
cd MultiProtocolDataCollector
```

### 2. 环境配置
```bash
# 复制环境配置文件
cp .env.example .env

# 编辑配置文件
vim .env
```

### 3. 启动服务
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

### 4. 访问系统
- **Web界面**: http://localhost
- **API文档**: http://localhost:8000/docs
- **默认账号**: admin / admin123

## 📚 详细文档

- [API文档](docs/API.md)
- [部署指南](docs/DEPLOYMENT.md)
- [用户手册](docs/USER_GUIDE.md)

## 🛠️ 开发

### 项目结构
```
MultiProtocolDataCollector/
├── backend/                 # 后端服务
│   ├── api-gateway/        # API网关
│   ├── task-scheduler/     # 任务调度器
│   ├── ssh-collector/      # SSH采集器
│   ├── api-collector/      # API采集器
│   ├── snmp-collector/     # SNMP采集器
│   ├── netmiko-ssh-collector/ # Netmiko SSH采集器
│   ├── go-ssh-collector/   # Go SSH采集器
│   └── common/            # 公共模块
├── frontend/               # 前端界面
├── database/              # 数据库脚本
├── docker/               # Docker配置
├── docs/                 # 文档
└── scripts/              # 脚本工具
```

### 本地开发
```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
cd backend/api-gateway
python app.py

# 启动前端开发服务器
cd frontend
npm install
npm start
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 联系我们

- 项目主页: https://github.com/tzwfy520/MultiProtocolDataCollector
- 问题反馈: https://github.com/tzwfy520/MultiProtocolDataCollector/issues

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者！