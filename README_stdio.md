# stdio 通信系统

这是一个基于标准输入输出（stdio）的进程间通信系统，支持服务器启动客户端和双向消息通信。

## 文件结构

```
image_ai/
├── main.py                    # 原有的主程序
├── client_for_server.py       # 客户端代码（被服务器启动）
├── server_launch_client.py    # 服务器代码（启动客户端）
├── test_stdio.py             # 测试脚本
└── README_stdio.md           # 本说明文档
```

## 功能特性

- **服务器启动客户端**：服务器进程自动启动客户端进程
- **双向通信**：支持客户端和服务器之间的双向消息传递
- **消息类型**：支持 ping、echo、calculate、shutdown 等消息类型
- **错误处理**：完整的错误处理和日志记录
- **进程管理**：自动管理客户端进程的生命周期

## 使用方法

### 1. 基本使用

```bash
# 启动服务器（会自动启动客户端）
python server_launch_client.py
```

服务器启动后，会显示可用的命令：
- `ping` - 发送 ping 消息
- `echo <文本>` - 发送 echo 消息
- `calc <表达式>` - 发送计算消息
- `shutdown` - 关闭服务器和客户端
- `quit` - 退出服务器

### 2. 独立测试客户端

```bash
# 独立启动客户端（用于测试）
python client_for_server.py
```

### 3. 运行测试

```bash
# 运行完整的测试套件
python test_stdio.py
```

## 通信协议

### 消息格式

所有消息使用 JSON 格式，每行一个 JSON 对象：

```json
{"type": "ping", "id": 1, "timestamp": 1234567890}
{"type": "echo", "id": 2, "message": "Hello World"}
{"type": "calculate", "id": 3, "expression": "2 + 3 * 4"}
```

### 支持的消息类型

#### 客户端 -> 服务器
- `client_ready` - 客户端就绪通知
- `pong` - ping 响应
- `echo_response` - echo 响应
- `calculation_result` - 计算结果
- `calculation_error` - 计算错误
- `shutdown_ack` - 关闭确认

#### 服务器 -> 客户端
- `server_ready` - 服务器就绪通知
- `ping` - ping 请求
- `echo` - echo 请求
- `calculate` - 计算请求
- `shutdown` - 关闭请求

## 工作原理

### 1. 进程启动

```
服务器进程 (server_launch_client.py)
    ↓ subprocess.Popen
客户端进程 (client_for_server.py)
```

### 2. 管道连接

```
服务器 stdin ←→ 客户端 stdout
服务器 stdout ←→ 客户端 stdin
```

### 3. 消息流程

1. 服务器启动客户端进程
2. 建立管道连接
3. 客户端发送 `client_ready` 消息
4. 服务器发送 `server_ready` 消息
5. 开始双向通信

## 环境变量

客户端支持以下环境变量：

- `LAUNCHED_BY_SERVER` - 标识是否被服务器启动
- `SERVER_PID` - 服务器进程 ID
- `CLIENT_ID` - 客户端标识符

## 扩展开发

### 添加新的消息类型

1. 在 `message_handlers` 字典中添加处理器
2. 实现对应的处理函数
3. 更新消息类型列表

### 添加新的客户端功能

1. 在客户端类中添加新的方法
2. 注册相应的消息处理器
3. 实现业务逻辑

## 故障排除

### 常见问题

1. **客户端无法启动**
   - 检查 Python 路径
   - 确认文件权限
   - 查看错误日志

2. **通信失败**
   - 检查管道连接
   - 确认消息格式
   - 查看进程状态

3. **进程异常退出**
   - 检查错误处理
   - 查看系统资源
   - 确认依赖库

### 调试技巧

1. 启用详细日志
2. 使用测试脚本验证
3. 检查进程状态
4. 监控系统资源

## 性能考虑

- 消息大小：避免发送过大的消息
- 频率控制：合理控制消息发送频率
- 资源管理：及时清理不需要的资源
- 错误恢复：实现错误重试机制

## 安全注意事项

- 输入验证：验证所有输入消息
- 权限控制：限制客户端权限
- 资源限制：设置合理的资源限制
- 日志记录：记录所有重要操作

## 许可证

本项目遵循原有项目的许可证条款。
