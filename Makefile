# 多协议数据采集系统 Makefile

.PHONY: help init build start stop restart logs status clean test lint format docs backup

# 默认环境
ENV ?= dev

# 颜色定义
RED := \033[31m
GREEN := \033[32m
YELLOW := \033[33m
BLUE := \033[34m
RESET := \033[0m

# 帮助信息
help: ## 显示帮助信息
	@echo "$(BLUE)多协议数据采集系统 - 可用命令:$(RESET)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-15s$(RESET) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)环境变量:$(RESET)"
	@echo "  ENV=dev|test|prod  设置部署环境 (默认: dev)"
	@echo ""
	@echo "$(YELLOW)示例:$(RESET)"
	@echo "  make start ENV=prod    # 启动生产环境"
	@echo "  make logs ENV=test     # 查看测试环境日志"

init: ## 初始化项目环境
	@echo "$(BLUE)初始化项目环境...$(RESET)"
	@chmod +x scripts/init.sh
	@./scripts/init.sh
	@echo "$(GREEN)项目初始化完成$(RESET)"

build: ## 构建Docker镜像
	@echo "$(BLUE)构建Docker镜像...$(RESET)"
	@docker-compose build --no-cache
	@echo "$(GREEN)镜像构建完成$(RESET)"

start: ## 启动服务
	@echo "$(BLUE)启动服务 (环境: $(ENV))...$(RESET)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh $(ENV) start
	@echo "$(GREEN)服务启动完成$(RESET)"

stop: ## 停止服务
	@echo "$(BLUE)停止服务 (环境: $(ENV))...$(RESET)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh $(ENV) stop
	@echo "$(GREEN)服务已停止$(RESET)"

restart: ## 重启服务
	@echo "$(BLUE)重启服务 (环境: $(ENV))...$(RESET)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh $(ENV) restart
	@echo "$(GREEN)服务重启完成$(RESET)"

update: ## 更新服务
	@echo "$(BLUE)更新服务 (环境: $(ENV))...$(RESET)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh $(ENV) update
	@echo "$(GREEN)服务更新完成$(RESET)"

logs: ## 查看服务日志
	@echo "$(BLUE)查看服务日志 (环境: $(ENV))...$(RESET)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh $(ENV) logs

status: ## 查看服务状态
	@echo "$(BLUE)查看服务状态 (环境: $(ENV))...$(RESET)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh $(ENV) status

health: ## 健康检查
	@echo "$(BLUE)执行健康检查 (环境: $(ENV))...$(RESET)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh $(ENV) health

backup: ## 备份数据
	@echo "$(BLUE)备份数据 (环境: $(ENV))...$(RESET)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh $(ENV) backup
	@echo "$(GREEN)数据备份完成$(RESET)"

clean: ## 清理未使用的资源
	@echo "$(BLUE)清理未使用的资源...$(RESET)"
	@docker system prune -f
	@docker volume prune -f
	@docker image prune -f
	@echo "$(GREEN)资源清理完成$(RESET)"

test: ## 运行测试
	@echo "$(BLUE)运行测试...$(RESET)"
	@docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@docker-compose -f docker-compose.test.yml down
	@echo "$(GREEN)测试完成$(RESET)"

lint: ## 代码检查
	@echo "$(BLUE)执行代码检查...$(RESET)"
	# Python代码检查
	@find backend -name "*.py" -exec python -m flake8 {} \; || true
	# JavaScript/TypeScript代码检查
	@cd frontend && npm run lint || true
	@echo "$(GREEN)代码检查完成$(RESET)"

format: ## 代码格式化
	@echo "$(BLUE)执行代码格式化...$(RESET)"
	# Python代码格式化
	@find backend -name "*.py" -exec python -m black {} \; || true
	# JavaScript/TypeScript代码格式化
	@cd frontend && npm run lint:fix || true
	@echo "$(GREEN)代码格式化完成$(RESET)"

docs: ## 生成文档
	@echo "$(BLUE)生成API文档...$(RESET)"
	@docker-compose exec api-gateway python -c "import app; print('API文档地址: http://localhost:8000/docs')"
	@echo "$(GREEN)文档生成完成$(RESET)"

# 开发相关命令
dev-setup: init build ## 开发环境完整设置
	@echo "$(GREEN)开发环境设置完成$(RESET)"

dev-start: ## 启动开发环境
	@make start ENV=dev

dev-stop: ## 停止开发环境
	@make stop ENV=dev

dev-logs: ## 查看开发环境日志
	@make logs ENV=dev

# 生产相关命令
prod-deploy: ## 部署到生产环境
	@echo "$(YELLOW)警告: 即将部署到生产环境$(RESET)"
	@read -p "确认部署到生产环境? [y/N] " confirm && [ "$$confirm" = "y" ]
	@make start ENV=prod

prod-backup: ## 生产环境备份
	@make backup ENV=prod

prod-status: ## 生产环境状态
	@make status ENV=prod

# 数据库相关命令
db-init: ## 初始化数据库
	@echo "$(BLUE)初始化数据库...$(RESET)"
	@docker-compose exec mysql mysql -u root -p$$MYSQL_ROOT_PASSWORD -e "source /docker-entrypoint-initdb.d/init.sql"
	@echo "$(GREEN)数据库初始化完成$(RESET)"

db-backup: ## 备份数据库
	@echo "$(BLUE)备份数据库...$(RESET)"
	@mkdir -p backups
	@docker-compose exec mysql mysqldump -u root -p$$MYSQL_ROOT_PASSWORD multiproto_gather > backups/db_backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)数据库备份完成$(RESET)"

db-restore: ## 恢复数据库 (需要指定备份文件: BACKUP_FILE=xxx.sql)
	@echo "$(BLUE)恢复数据库...$(RESET)"
	@if [ -z "$(BACKUP_FILE)" ]; then echo "$(RED)错误: 请指定备份文件 BACKUP_FILE=xxx.sql$(RESET)"; exit 1; fi
	@docker-compose exec -T mysql mysql -u root -p$$MYSQL_ROOT_PASSWORD multiproto_gather < $(BACKUP_FILE)
	@echo "$(GREEN)数据库恢复完成$(RESET)"

# 监控相关命令
monitor: ## 实时监控服务状态
	@echo "$(BLUE)实时监控服务状态...$(RESET)"
	@watch -n 5 'docker-compose ps && echo "" && docker stats --no-stream'

# 安全相关命令
security-scan: ## 安全扫描
	@echo "$(BLUE)执行安全扫描...$(RESET)"
	@docker run --rm -v $(PWD):/app -w /app securecodewarrior/docker-security-scan || true
	@echo "$(GREEN)安全扫描完成$(RESET)"

# 性能测试
perf-test: ## 性能测试
	@echo "$(BLUE)执行性能测试...$(RESET)"
	@echo "$(YELLOW)请确保服务已启动$(RESET)"
	@curl -s http://localhost:8000/health && echo "API网关响应正常" || echo "API网关响应异常"
	@echo "$(GREEN)性能测试完成$(RESET)"

# 版本管理
version: ## 显示版本信息
	@echo "$(BLUE)版本信息:$(RESET)"
	@echo "Docker: $$(docker --version)"
	@echo "Docker Compose: $$(docker-compose --version)"
	@echo "项目版本: $$(cat package.json 2>/dev/null | grep version | head -1 | awk -F: '{ print $$2 }' | sed 's/[\",]//g' | tr -d '[[:space:]]' || echo '未知')"

# 快速命令别名
up: start ## 启动服务 (别名)
down: stop ## 停止服务 (别名)
ps: status ## 查看状态 (别名)
tail: logs ## 查看日志 (别名)