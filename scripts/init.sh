#!/bin/bash

# 多协议数据采集系统初始化脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# 检查操作系统
check_os() {
    log_info "检查操作系统..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
        log_info "检测到 Linux 系统"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
        log_info "检测到 macOS 系统"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
        log_info "检测到 Windows 系统"
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
}

# 检查并安装Docker
install_docker() {
    log_info "检查 Docker 安装状态..."
    
    if command -v docker &> /dev/null; then
        log_success "Docker 已安装: $(docker --version)"
        return 0
    fi
    
    log_warning "Docker 未安装，开始安装..."
    
    case $OS in
        "linux")
            # Ubuntu/Debian
            if command -v apt-get &> /dev/null; then
                sudo apt-get update
                sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
                echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io
            # CentOS/RHEL
            elif command -v yum &> /dev/null; then
                sudo yum install -y yum-utils
                sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
                sudo yum install -y docker-ce docker-ce-cli containerd.io
            else
                log_error "不支持的 Linux 发行版"
                exit 1
            fi
            
            # 启动Docker服务
            sudo systemctl start docker
            sudo systemctl enable docker
            
            # 添加用户到docker组
            sudo usermod -aG docker $USER
            ;;
        "macos")
            log_info "请手动安装 Docker Desktop for Mac"
            log_info "下载地址: https://www.docker.com/products/docker-desktop"
            exit 1
            ;;
        "windows")
            log_info "请手动安装 Docker Desktop for Windows"
            log_info "下载地址: https://www.docker.com/products/docker-desktop"
            exit 1
            ;;
    esac
    
    log_success "Docker 安装完成"
}

# 检查并安装Docker Compose
install_docker_compose() {
    log_info "检查 Docker Compose 安装状态..."
    
    if command -v docker-compose &> /dev/null; then
        log_success "Docker Compose 已安装: $(docker-compose --version)"
        return 0
    fi
    
    log_warning "Docker Compose 未安装，开始安装..."
    
    case $OS in
        "linux")
            # 下载最新版本的docker-compose
            COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d'"' -f4)
            sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
            sudo chmod +x /usr/local/bin/docker-compose
            ;;
        "macos")
            # macOS通常随Docker Desktop一起安装
            log_info "Docker Compose 通常随 Docker Desktop 一起安装"
            ;;
        "windows")
            # Windows通常随Docker Desktop一起安装
            log_info "Docker Compose 通常随 Docker Desktop 一起安装"
            ;;
    esac
    
    log_success "Docker Compose 安装完成"
}

# 创建项目目录结构
create_directories() {
    log_info "创建项目目录结构..."
    
    local dirs=(
        "logs"
        "data/mysql"
        "data/redis"
        "backups"
        "ssl"
        "uploads"
    )
    
    for dir in "${dirs[@]}"; do
        if [ ! -d "$dir" ]; then
            mkdir -p "$dir"
            log_info "创建目录: $dir"
        fi
    done
    
    log_success "目录结构创建完成"
}

# 设置环境文件
setup_env_file() {
    log_info "设置环境配置文件..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log_info "已复制 .env.example 到 .env"
        else
            log_error "找不到 .env.example 文件"
            exit 1
        fi
    else
        log_info ".env 文件已存在"
    fi
    
    # 生成随机密钥
    if command -v openssl &> /dev/null; then
        SECRET_KEY=$(openssl rand -hex 32)
        JWT_SECRET=$(openssl rand -hex 32)
        
        # 更新.env文件中的密钥
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            sed -i '' "s/your_secret_key_here/$SECRET_KEY/g" .env
            sed -i '' "s/your_jwt_secret_here/$JWT_SECRET/g" .env
        else
            # Linux
            sed -i "s/your_secret_key_here/$SECRET_KEY/g" .env
            sed -i "s/your_jwt_secret_here/$JWT_SECRET/g" .env
        fi
        
        log_success "已生成随机密钥"
    else
        log_warning "未找到 openssl，请手动设置 .env 文件中的密钥"
    fi
}

# 设置文件权限
set_permissions() {
    log_info "设置文件权限..."
    
    # 设置脚本执行权限
    chmod +x scripts/*.sh
    
    # 设置数据目录权限
    if [ -d "data" ]; then
        chmod -R 755 data
    fi
    
    # 设置日志目录权限
    if [ -d "logs" ]; then
        chmod -R 755 logs
    fi
    
    log_success "文件权限设置完成"
}

# 验证安装
verify_installation() {
    log_info "验证安装..."
    
    # 检查Docker
    if ! docker --version &> /dev/null; then
        log_error "Docker 验证失败"
        exit 1
    fi
    
    # 检查Docker Compose
    if ! docker-compose --version &> /dev/null; then
        log_error "Docker Compose 验证失败"
        exit 1
    fi
    
    # 检查环境文件
    if [ ! -f ".env" ]; then
        log_error "环境文件验证失败"
        exit 1
    fi
    
    log_success "安装验证通过"
}

# 显示后续步骤
show_next_steps() {
    log_success "初始化完成！"
    echo
    log_info "后续步骤:"
    echo "1. 检查并修改 .env 文件中的配置"
    echo "2. 运行 './scripts/deploy.sh dev start' 启动开发环境"
    echo "3. 访问 http://localhost 查看前端界面"
    echo "4. 访问 http://localhost:8000/docs 查看API文档"
    echo
    log_info "常用命令:"
    echo "  ./scripts/deploy.sh dev start    # 启动开发环境"
    echo "  ./scripts/deploy.sh dev stop     # 停止服务"
    echo "  ./scripts/deploy.sh dev logs     # 查看日志"
    echo "  ./scripts/deploy.sh dev status   # 查看状态"
}

# 主函数
main() {
    log_info "开始初始化多协议数据采集系统..."
    
    check_os
    install_docker
    install_docker_compose
    create_directories
    setup_env_file
    set_permissions
    verify_installation
    show_next_steps
}

# 执行主函数
main "$@"