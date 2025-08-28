# MCP 客户端初始化模块

这个模块提供了完整的 MCP (Model Context Protocol) 客户端初始化功能，可以轻松地在其他项目中使用。

## 文件结构

- `mcp_client_init.py` - 主要的 MCP 客户端初始化模块
- `example_usage.py` - 使用示例和演示代码
- `README_mcp_client.md` - 本说明文档

## 主要功能

### 1. MCP 客户端初始化
- 自动配置 MQTT 连接
- 支持自定义回调函数
- 自动发现和连接 MCP 服务器

### 2. 工具管理
- 自动获取 MCP 服务器提供的工具
- 将 MCP 工具转换为 LlamaIndex 兼容格式
- 支持工具调用和结果处理

### 3. 连接管理
- 自动重连机制
- 连接状态监控
- 优雅的关闭处理

## 快速开始

### 基本使用

```python
from mcp_client_init import initialize_mcp_client, get_mcp_tools

async def main():
    # 初始化 MCP 客户端
    mcp_client = await initialize_mcp_client(
        client_name="my_client",
        host="localhost"
    )
    
    # 获取可用工具
    tools = await get_mcp_tools(mcp_client)
    
    # 使用完毕后关闭
    await mcp_client.stop()
```

### 自定义回调函数

```python
async def custom_on_connect(client, server_name, connect_result):
    print(f"连接到 {server_name} 成功！")

async def custom_on_discover(client, server_name):
    print(f"发现服务器: {server_name}")

# 使用自定义回调
mcp_client = await initialize_mcp_client(
    client_name="custom_client",
    host="localhost"
)

# 设置回调函数
mcp_client.on_mcp_connect = custom_on_connect
mcp_client.on_mcp_server_discovered = custom_on_discover
```

## API 参考

### 主要函数

#### `initialize_mcp_client(client_name, host, wait_time)`
初始化并启动 MCP 客户端。

**参数:**
- `client_name` (str): 客户端名称
- `host` (str): MQTT 服务器主机地址
- `wait_time` (float): 等待连接建立的时间（秒）

**返回:**
- `mcp_mqtt.MqttTransportClient`: 已启动的 MCP 客户端实例

#### `get_mcp_tools(mcp_client, server_name)`
获取 MCP 服务器提供的工具列表。

**参数:**
- `mcp_client`: MCP 客户端实例
- `server_name` (str): 服务器名称

**返回:**
- `List[BaseTool]`: LlamaIndex 兼容的工具列表

#### `create_mcp_client(client_name, host, auto_connect_to_mcp_server, on_mcp_server_discovered, on_mcp_connect, on_mcp_disconnect)`
创建 MCP 客户端实例（不自动启动）。

**参数:**
- `client_name` (str): 客户端名称
- `host` (str): MQTT 服务器主机地址
- `auto_connect_to_mcp_server` (bool): 是否自动连接
- `on_mcp_server_discovered`: 服务器发现回调
- `on_mcp_connect`: 连接成功回调
- `on_mcp_disconnect`: 断开连接回调

### 回调函数

#### `on_mcp_server_discovered(client, server_name)`
当发现新的 MCP 服务器时调用。

#### `on_mcp_connect(client, server_name, connect_result)`
当成功连接到 MCP 服务器时调用。

#### `on_mcp_disconnect(client, server_name)`
当与 MCP 服务器断开连接时调用。

## 集成到现有项目

### 1. 复制模块文件
将 `mcp_client_init.py` 复制到你的项目中。

### 2. 安装依赖
确保安装了必要的依赖包：

```bash
pip install mcp-client mcp-shared anyio llama-index
```

### 3. 导入和使用
```python
from mcp_client_init import initialize_mcp_client, get_mcp_tools

# 在你的代码中使用
```

## 错误处理

模块包含完整的错误处理机制：

- 连接失败时自动重试
- 工具调用失败时的优雅降级
- 详细的日志记录
- 异常传播和错误信息

## 配置选项

### 环境变量
- `MCP_HOST`: MQTT 服务器主机地址
- `MCP_CLIENT_NAME`: 默认客户端名称
- `MCP_LOG_LEVEL`: 日志级别

### 日志配置
默认日志级别为 DEBUG，可以通过以下方式修改：

```python
import logging
logging.getLogger('mcp_client_init').setLevel(logging.INFO)
```

## 故障排除

### 常见问题

1. **连接失败**
   - 检查 MQTT 服务器是否运行
   - 确认主机地址和端口正确
   - 检查网络连接

2. **工具获取失败**
   - 确认 MCP 服务器正在运行
   - 检查服务器名称是否正确
   - 查看日志中的错误信息

3. **性能问题**
   - 调整 `wait_time` 参数
   - 检查网络延迟
   - 优化回调函数

## 示例项目

查看 `example_usage.py` 文件获取完整的使用示例，包括：

- 基本客户端初始化
- 自定义回调函数
- 工具集成
- 错误处理

## 许可证

本模块遵循与原项目相同的许可证。

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个模块。
