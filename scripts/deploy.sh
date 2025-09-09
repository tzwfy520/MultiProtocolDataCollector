#!/bin/bash

# 多协议数据采集系统部署脚本
# 使用方法: ./deploy.sh [环境] [操作]
# 环境: dev|test|prod
# 操作: start|stop|restart|update|logs|status

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
PROJECT_NAME="multiproto-gather"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# 函数定义
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    log_success "依赖检查完成"
}

# 检查环境文件
check_env_file() {
    local env=$1
    local env_file=".env.${env}"
    
    if [ "$env" = "dev" ]; then
        env_file=".env.example"
    fi
    
    if [ ! -f "$env_file" ]; then
        log_warning "环境文件 $env_file 不存在，使用 .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example $ENV_FILE
            log_info "已复制 .env.example 到 $ENV_FILE"
        else
            log_error "找不到环境配置文件"
            exit 1
        fi
    else
        cp $env_file $ENV_FILE
        log_info "使用环境文件: $env_file"
    fi
}

# 构建镜像
build_images() {
    log_info "构建 Docker 镜像..."
    docker-compose -f $DOCKER_COMPOSE_FILE build --no-cache
    log_success "镜像构建完成"
}

# 启动服务
start_services() {
    log_info "启动服务..."
    docker-compose -f $DOCKER_COMPOSE_FILE up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10
    
    # 检查服务状态
    check_services_health
}

# 停止服务
stop_services() {
    log_info "停止服务..."
    docker-compose -f $DOCKER_COMPOSE_FILE down
    log_success "服务已停止"
}

# 重启服务
restart_services() {
    log_info "重启服务..."
    stop_services
    start_services
}

# 更新服务
update_services() {
    log_info "更新服务..."
    
    # 拉取最新代码
    if [ -d ".git" ]; then
        log_info "拉取最新代码..."
        git pull origin main
    fi
    
    # 重新构建并启动
    build_images
    restart_services
}

# 查看日志
view_logs() {
    local service=$1
    if [ -z "$service" ]; then
        docker-compose -f $DOCKER_COMPOSE_FILE logs -f
    else
        docker-compose -f $DOCKER_COMPOSE_FILE logs -f $service
    fi
}

# 检查服务健康状态
check_services_health() {
    log_info "检查服务健康状态..."
    
    local services=("api-gateway" "mysql" "redis" "ssh-collector" "go-ssh-collector" "api-collector" "snmp-collector" "netmiko-ssh-collector" "task-scheduler")
    local healthy_count=0
    
    for service in "${services[@]}"; do
        if docker-compose -f $DOCKER_COMPOSE_FILE ps $service | grep -q "Up"; then
            log_success "$service: 运行中"
            ((healthy_count++))
        else
            log_error "$service: 未运行"
        fi
    done
    
    log_info "健康服务数量: $healthy_count/${#services[@]}"
    
    # 检查API端点
    log_info "检查API端点..."
    sleep 5
    
    if curl -s http://localhost:8000/health > /dev/null; then
        log_success "API网关健康检查通过"
    else
        log_warning "API网关健康检查失败"
    fi
}

# 显示服务状态
show_status() {
    log_info "服务状态:"
    docker-compose -f $DOCKER_COMPOSE_FILE ps
    
    echo
    log_info "资源使用情况:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"
}

# 清理资源
cleanup() {
    log_info "清理未使用的资源..."
    docker system prune -f
    docker volume prune -f
    log_success "清理完成"
}

# 备份数据
backup_data() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p $backup_dir
    
    log_info "备份数据到 $backup_dir..."
    
    # 备份数据库
    docker-compose -f $DOCKER_COMPOSE_FILE exec -T mysql mysqldump -u root -p\$MYSQL_ROOT_PASSWORD multiproto_gather > $backup_dir/database.sql
    
    # 备份配置文件
    cp $ENV_FILE $backup_dir/
    cp $DOCKER_COMPOSE_FILE $backup_dir/
    
    log_success "数据备份完成: $backup_dir"
}

# 显示帮助信息
show_help() {
    echo "多协议数据采集系统部署脚本"
    echo
    echo "使用方法:"
    echo "  $0 [环境] [操作] [参数]"
    echo
    echo "环境:"
    echo "  dev     开发环境"
    echo "  test    测试环境"
    echo "  prod    生产环境"
    echo
    echo "操作:"
    echo "  start   启动服务"
    echo "  stop    停止服务"
    echo "  restart 重启服务"
    echo "  update  更新服务"
    echo "  build   构建镜像"
    echo "  logs    查看日志 [服务名]"
    echo "  status  显示状态"
    echo "  health  健康检查"
    echo "  backup  备份数据"
    echo "  cleanup 清理资源"
    echo "  help    显示帮助"
    echo
    echo "示例:"
    echo "  $0 dev start          # 启动开发环境"
    echo "  $0 prod restart       # 重启生产环境"
    echo "  $0 test logs mysql    # 查看测试环境MySQL日志"
}

# 主函数
main() {
    local env=${1:-dev}
    local action=${2:-help}
    local param=$3
    
    # 检查参数
    if [ "$action" = "help" ] || [ "$1" = "help" ] || [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    # 验证环境参数
    if [[ ! "$env" =~ ^(dev|test|prod)$ ]]; then
        log_error "无效的环境参数: $env"
        show_help
        exit 1
    fi
    
    log_info "环境: $env, 操作: $action"
    
    # 检查依赖
    check_dependencies
    
    # 设置环境文件
    check_env_file $env
    
    # 执行操作
    case $action in
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "update")
            update_services
            ;;
        "build")
            build_images
            ;;
        "logs")
            view_logs $param
            ;;
        "status")
            show_status
            ;;
        "health")
            check_services_health
            ;;
        "backup")
            backup_data
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            log_error "未知操作: $action"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"