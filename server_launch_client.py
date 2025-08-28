#!/usr/bin/env python3
import json
import subprocess
import threading
import time
import logging
import sys
from typing import Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - SERVER - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StdioServerLaunchClient:
    def __init__(self, client_command: list):
        """
        初始化服务器 - 启动客户端模式
        
        Args:
            client_command: 启动客户端的命令列表，如 ["python", "client_for_server.py"]
        """
        self.client_command = client_command
        self.client_process: Optional[subprocess.Popen] = None
        self.running = False
        self.message_handlers = {
            "ping": self.handle_ping,
            "echo": self.handle_echo,
            "calculate": self.handle_calculate,
            "shutdown": self.handle_shutdown
        }
        
        # 客户端连接状态
        self.client_connected = False
        self.client_ready = False
    
    def start_client(self):
        """启动客户端进程"""
        try:
            logger.info("正在启动客户端进程...")
            
            # 启动客户端进程，建立管道连接
            self.client_process = subprocess.Popen(
                self.client_command,
                stdin=subprocess.PIPE,      # 客户端写入，服务器读取
                stdout=subprocess.PIPE,     # 服务器写入，客户端读取
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            logger.info("客户端进程已启动")
            
            # 启动客户端消息接收线程
            client_receive_thread = threading.Thread(target=self._receive_from_client, daemon=True)
            client_receive_thread.start()
            
            # 等待客户端就绪
            time.sleep(1)
            
            return True
            
        except Exception as e:
            logger.error(f"启动客户端失败: {e}")
            return False
    
    def _receive_from_client(self):
        """从客户端接收消息的线程函数"""
        while self.running and self.client_process:
            try:
                if self.client_process.stdout:
                    line = self.client_process.stdout.readline().strip()
                    if line:
                        try:
                            message = json.loads(line)
                            self._handle_client_message(message)
                        except json.JSONDecodeError:
                            logger.warning(f"无法解析客户端 JSON: {line}")
                        except Exception as e:
                            logger.error(f"处理客户端消息时发生错误: {e}")
                
                # 检查客户端进程状态
                if self.client_process.poll() is not None:
                    logger.info("客户端进程已退出")
                    self.client_connected = False
                    self.client_ready = False
                    break
                    
            except Exception as e:
                logger.error(f"从客户端接收消息时发生错误: {e}")
                break
        
        self.client_connected = False
        self.client_ready = False
    
    def _handle_client_message(self, message: Dict[str, Any]):
        """处理来自客户端的消息"""
        message_type = message.get("type")
        
        if message_type == "client_ready":
            logger.info("客户端已就绪")
            self.client_ready = True
            self.client_connected = True
        elif message_type == "ping":
            self.handle_ping(message)
        elif message_type == "echo":
            self.handle_echo(message)
        elif message_type == "calculate":
            self.handle_calculate(message)
        elif message_type == "shutdown":
            self.handle_shutdown(message)
        else:
            logger.info(f"收到客户端消息: {message}")
    
    def send_to_client(self, message: Dict[str, Any]) -> bool:
        """向客户端发送消息"""
        try:
            if not self.client_process or not self.client_process.stdin:
                logger.error("客户端进程未启动或 stdin 不可用")
                return False
            
            json_message = json.dumps(message, ensure_ascii=False)
            self.client_process.stdin.write(json_message + "\n")
            self.client_process.stdin.flush()
            
            logger.info(f"发送到客户端: {json_message}")
            return True
            
        except Exception as e:
            logger.error(f"发送到客户端失败: {e}")
            return False
    
    def handle_ping(self, data: Dict[str, Any]):
        """处理 ping 消息"""
        response = {
            "type": "pong",
            "id": data.get("id"),
            "timestamp": data.get("timestamp"),
            "message": "pong from server"
        }
        self.send_to_client(response)
    
    def handle_echo(self, data: Dict[str, Any]):
        """处理 echo 消息"""
        response = {
            "type": "echo_response",
            "id": data.get("id"),
            "original_message": data.get("message"),
            "echoed_message": f"Server echoes: {data.get('message')}"
        }
        self.send_to_client(response)
    
    def handle_calculate(self, data: Dict[str, Any]):
        """处理计算消息"""
        try:
            expression = data.get("expression", "")
            result = eval(expression)
            
            response = {
                "type": "calculation_result",
                "id": data.get("id"),
                "expression": expression,
                "result": result
            }
        except Exception as e:
            response = {
                "type": "calculation_error",
                "id": data.get("id"),
                "expression": data.get("expression"),
                "error": str(e)
            }
        
        self.send_to_client(response)
    
    def handle_shutdown(self, data: Dict[str, Any]):
        """处理关闭消息"""
        logger.info("收到关闭请求")
        self.running = False
        response = {
            "type": "shutdown_ack",
            "id": data.get("id"),
            "message": "Server shutting down"
        }
        self.send_to_client(response)
    
    def run(self):
        """运行服务器主循环"""
        logger.info("stdio 服务器启动（启动客户端模式）")
        
        # 启动客户端
        if not self.start_client():
            logger.error("无法启动客户端，服务器退出")
            return
        
        # 等待客户端就绪
        while not self.client_ready and self.running:
            time.sleep(0.1)
            if self.client_process and self.client_process.poll() is not None:
                logger.error("客户端进程异常退出")
                return
        
        logger.info("客户端已连接，开始处理消息")
        
        # 发送服务器就绪消息
        self.send_to_client({
            "type": "server_ready",
            "message": "Server is ready to receive messages",
            "supported_types": list(self.message_handlers.keys())
        })
        
        # 主循环 - 处理用户输入
        print("\n" + "="*50)
        print("服务器已启动，客户端已连接")
        print("可用命令：")
        print("  ping     - 发送 ping 消息")
        print("  echo <文本> - 发送 echo 消息")
        print("  calc <表达式> - 发送计算消息")
        print("  shutdown - 关闭服务器和客户端")
        print("  quit     - 退出服务器")
        print("="*50)
        
        while self.running:
            try:
                user_input = input("\n请输入命令: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() == "quit":
                    break
                elif user_input.lower() == "ping":
                    self.send_to_client({
                        "type": "ping",
                        "timestamp": time.time()
                    })
                elif user_input.lower().startswith("echo "):
                    text = user_input[5:].strip()
                    if text:
                        self.send_to_client({
                            "type": "echo",
                            "message": text
                        })
                    else:
                        print("请输入要 echo 的文本")
                elif user_input.lower().startswith("calc "):
                    expression = user_input[5:].strip()
                    if expression:
                        self.send_to_client({
                            "type": "calculate",
                            "expression": expression
                        })
                    else:
                        print("请输入要计算的表达式")
                elif user_input.lower() == "shutdown":
                    self.send_to_client({
                        "type": "shutdown"
                    })
                    break
                else:
                    print("未知命令，请使用：ping, echo <文本>, calc <表达式>, shutdown, quit")
                
                time.sleep(0.5)
                
            except KeyboardInterrupt:
                break
            except EOFError:
                break
        
        logger.info("服务器关闭")
    
    def stop(self):
        """停止服务器"""
        logger.info("正在停止服务器...")
        self.running = False
        
        if self.client_process:
            try:
                # 发送关闭信号
                self.send_to_client({
                    "type": "shutdown"
                })
                
                # 等待进程结束
                time.sleep(1)
                
                if self.client_process.poll() is None:
                    self.client_process.terminate()
                    self.client_process.wait(timeout=5)
                    
            except Exception as e:
                logger.error(f"停止客户端进程时发生错误: {e}")
            
            finally:
                self.client_process = None

if __name__ == "__main__":
    server = StdioServerLaunchClient(["python", "client_for_server.py"])
    
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("收到中断信号")
    except Exception as e:
        logger.error(f"运行时发生错误: {e}")
    finally:
        server.stop()
