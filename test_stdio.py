#!/usr/bin/env python3
"""
stdio 通信测试脚本
用于测试客户端和服务器之间的通信功能
"""

import subprocess
import time
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - TEST - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_stdio_communication():
    """测试 stdio 通信功能"""
    logger.info("开始测试 stdio 通信功能")
    
    try:
        # 启动服务器（服务器会自动启动客户端）
        logger.info("启动服务器...")
        server_process = subprocess.Popen(
            ["python", "server_launch_client.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 等待服务器启动
        time.sleep(3)
        
        # 检查进程状态
        if server_process.poll() is not None:
            logger.error("服务器进程异常退出")
            return False
        
        logger.info("服务器启动成功")
        
        # 发送测试命令
        test_commands = [
            "ping",
            "echo Hello World",
            "calc 2 + 3 * 4",
            "calc 10 / 0",  # 测试错误处理
            "shutdown"
        ]
        
        for cmd in test_commands:
            logger.info(f"发送命令: {cmd}")
            server_process.stdin.write(cmd + "\n")
            server_process.stdin.flush()
            
            # 等待响应
            time.sleep(1)
            
            # 读取输出
            while True:
                try:
                    line = server_process.stdout.readline().strip()
                    if line:
                        logger.info(f"服务器输出: {line}")
                    else:
                        break
                except:
                    break
        
        # 等待进程结束
        logger.info("等待服务器关闭...")
        server_process.wait(timeout=10)
        
        logger.info("测试完成")
        return True
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        return False
    finally:
        # 确保进程被清理
        if 'server_process' in locals() and server_process.poll() is None:
            server_process.terminate()
            server_process.wait(timeout=5)

def test_client_standalone():
    """测试客户端独立运行"""
    logger.info("测试客户端独立运行")
    
    try:
        # 启动客户端
        client_process = subprocess.Popen(
            ["python", "client_for_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 等待客户端启动
        time.sleep(2)
        
        # 检查进程状态
        if client_process.poll() is not None:
            logger.error("客户端进程异常退出")
            return False
        
        logger.info("客户端启动成功")
        
        # 发送测试消息
        test_messages = [
            {"type": "ping", "timestamp": time.time()},
            {"type": "echo", "message": "Test message"},
            {"type": "calculate", "expression": "1 + 1"},
            {"type": "shutdown"}
        ]
        
        for msg in test_messages:
            logger.info(f"发送消息: {msg}")
            json_msg = json.dumps(msg)
            client_process.stdin.write(json_msg + "\n")
            client_process.stdin.flush()
            
            # 等待响应
            time.sleep(0.5)
            
            # 读取输出
            try:
                line = client_process.stdout.readline().strip()
                if line:
                    logger.info(f"客户端输出: {line}")
            except:
                pass
        
        # 等待进程结束
        logger.info("等待客户端关闭...")
        client_process.wait(timeout=10)
        
        logger.info("客户端独立测试完成")
        return True
        
    except Exception as e:
        logger.error(f"客户端测试过程中发生错误: {e}")
        return False
    finally:
        # 确保进程被清理
        if 'client_process' in locals() and client_process.poll() is None:
            client_process.terminate()
            client_process.wait(timeout=5)

def main():
    """主测试函数"""
    logger.info("=" * 50)
    logger.info("stdio 通信系统测试")
    logger.info("=" * 50)
    
    # 测试1：完整的服务器-客户端通信
    logger.info("\n测试1: 服务器启动客户端通信")
    success1 = test_stdio_communication()
    
    # 测试2：客户端独立运行
    logger.info("\n测试2: 客户端独立运行")
    success2 = test_client_standalone()
    
    # 测试结果
    logger.info("\n" + "=" * 50)
    logger.info("测试结果汇总")
    logger.info("=" * 50)
    logger.info(f"测试1 (服务器启动客户端): {'通过' if success1 else '失败'}")
    logger.info(f"测试2 (客户端独立运行): {'通过' if success2 else '失败'}")
    
    if success1 and success2:
        logger.info("所有测试通过！stdio 通信系统工作正常。")
    else:
        logger.error("部分测试失败，请检查代码和配置。")

if __name__ == "__main__":
    main()
