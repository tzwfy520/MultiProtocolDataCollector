package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	"golang.org/x/crypto/ssh"
)

type SSHConnection struct {
	Client    *ssh.Client
	Config    SSHConfig
	CreatedAt time.Time
}

type SSHConfig struct {
	Host     string `json:"host" binding:"required"`
	Port     int    `json:"port"`
	Username string `json:"username" binding:"required"`
	Password string `json:"password" binding:"required"`
	Timeout  int    `json:"timeout"`
}

type CommandRequest struct {
	ConnectionID string `json:"connection_id" binding:"required"`
	Command      string `json:"command" binding:"required"`
}

type CommandResult struct {
	Command   string    `json:"command"`
	Output    string    `json:"output"`
	Error     string    `json:"error,omitempty"`
	Timestamp time.Time `json:"timestamp"`
}

type SSHCollector struct {
	connections map[string]*SSHConnection
	mutex       sync.RWMutex
}

func NewSSHCollector() *SSHCollector {
	return &SSHCollector{
		connections: make(map[string]*SSHConnection),
	}
}

func (sc *SSHCollector) Connect(config SSHConfig) (string, error) {
	// 设置默认值
	if config.Port == 0 {
		config.Port = 22
	}
	if config.Timeout == 0 {
		config.Timeout = 30
	}

	// SSH客户端配置
	sshConfig := &ssh.ClientConfig{
		User: config.Username,
		Auth: []ssh.AuthMethod{
			ssh.Password(config.Password),
		},
		HostKeyCallback: ssh.InsecureIgnoreHostKey(),
		Timeout:         time.Duration(config.Timeout) * time.Second,
	}

	// 建立连接
	address := fmt.Sprintf("%s:%d", config.Host, config.Port)
	client, err := ssh.Dial("tcp", address, sshConfig)
	if err != nil {
		return "", fmt.Errorf("failed to connect: %v", err)
	}

	// 生成连接ID
	connectionID := fmt.Sprintf("%s:%d:%s", config.Host, config.Port, config.Username)

	// 存储连接
	sc.mutex.Lock()
	sc.connections[connectionID] = &SSHConnection{
		Client:    client,
		Config:    config,
		CreatedAt: time.Now(),
	}
	sc.mutex.Unlock()

	return connectionID, nil
}

func (sc *SSHCollector) ExecuteCommand(connectionID, command string) (*CommandResult, error) {
	sc.mutex.RLock()
	conn, exists := sc.connections[connectionID]
	sc.mutex.RUnlock()

	if !exists {
		return nil, fmt.Errorf("connection not found")
	}

	// 创建会话
	session, err := conn.Client.NewSession()
	if err != nil {
		return nil, fmt.Errorf("failed to create session: %v", err)
	}
	defer session.Close()

	// 执行命令
	output, err := session.CombinedOutput(command)

	result := &CommandResult{
		Command:   command,
		Output:    string(output),
		Timestamp: time.Now(),
	}

	if err != nil {
		result.Error = err.Error()
	}

	return result, nil
}

func (sc *SSHCollector) Disconnect(connectionID string) error {
	sc.mutex.Lock()
	defer sc.mutex.Unlock()

	conn, exists := sc.connections[connectionID]
	if !exists {
		return fmt.Errorf("connection not found")
	}

	err := conn.Client.Close()
	delete(sc.connections, connectionID)

	return err
}

func (sc *SSHCollector) ListConnections() map[string]interface{} {
	sc.mutex.RLock()
	defer sc.mutex.RUnlock()

	connections := make(map[string]interface{})
	for id, conn := range sc.connections {
		connections[id] = map[string]interface{}{
			"host":       conn.Config.Host,
			"port":       conn.Config.Port,
			"username":   conn.Config.Username,
			"created_at": conn.CreatedAt,
		}
	}

	return connections
}

var collector *SSHCollector

func main() {
	collector = NewSSHCollector()

	// 设置Gin模式
	if os.Getenv("GIN_MODE") == "" {
		gin.SetMode(gin.ReleaseMode)
	}

	r := gin.Default()

	// CORS配置
	config := cors.DefaultConfig()
	config.AllowAllOrigins = true
	config.AllowMethods = []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"}
	config.AllowHeaders = []string{"*"}
	r.Use(cors.New(config))

	// 健康检查
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"status":             "healthy",
			"timestamp":          time.Now(),
			"service":            "go-ssh-collector",
			"active_connections": len(collector.connections),
		})
	})

	// 建立连接
	r.POST("/connect", func(c *gin.Context) {
		var config SSHConfig
		if err := c.ShouldBindJSON(&config); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		connectionID, err := collector.Connect(config)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"connection_id": connectionID,
			"status":        "connected",
			"timestamp":     time.Now(),
		})
	})

	// 执行命令
	r.POST("/execute", func(c *gin.Context) {
		var req CommandRequest
		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		result, err := collector.ExecuteCommand(req.ConnectionID, req.Command)
		if err != nil {
			c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, result)
	})

	// 断开连接
	r.POST("/disconnect", func(c *gin.Context) {
		var req struct {
			ConnectionID string `json:"connection_id" binding:"required"`
		}

		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
			return
		}

		err := collector.Disconnect(req.ConnectionID)
		if err != nil {
			c.JSON(http.StatusNotFound, gin.H{"error": err.Error()})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"status":    "disconnected",
			"timestamp": time.Now(),
		})
	})

	// 列出连接
	r.GET("/connections", func(c *gin.Context) {
		connections := collector.ListConnections()

		c.JSON(http.StatusOK, gin.H{
			"active_connections": connections,
			"count":              len(connections),
			"timestamp":          time.Now(),
		})
	})

	// 启动服务器
	port := os.Getenv("PORT")
	if port == "" {
		port = "8022"
	}

	log.Printf("Starting Go SSH Collector on port %s", port)
	log.Fatal(r.Run(":" + port))
}