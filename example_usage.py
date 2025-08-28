#!/usr/bin/env python3
"""
MCP 客户端使用示例
展示如何使用 mcp_client_init.py 模块来初始化和使用 MCP 客户端
"""

import asyncio
import anyio
from mcp_client_init import (
    initialize_mcp_client,
    get_mcp_tools,
    on_mcp_server_discovered,
    on_mcp_connect,
    on_mcp_disconnect,
)


async def simple_mcp_usage():
    """简单的 MCP 客户端使用示例"""
    try:
        print("正在初始化 MCP 客户端...")

        # 使用默认配置初始化 MCP 客户端
        mcp_client = await initialize_mcp_client(
            client_name="simple_client", host="localhost", wait_time=3.0
        )

        print("MCP 客户端初始化成功！")

        # 获取可用的工具
        tools = await get_mcp_tools(mcp_client)
        print(f"发现 {len(tools)} 个 MCP 工具:")

        for i, tool in enumerate(tools, 1):
            tool_name = getattr(tool.metadata, "name", str(tool))
            tool_desc = getattr(tool.metadata, "description", "无描述")
            print(f"  {i}. {tool_name}: {tool_desc}")

        # 使用完毕后关闭客户端
        await mcp_client.stop()
        print("MCP 客户端已关闭")

    except Exception as e:
        print(f"使用过程中出现错误: {e}")


async def custom_callback_mcp_usage():
    """使用自定义回调函数的 MCP 客户端示例"""

    async def custom_on_connect(client, server_name, connect_result):
        print(f"🎉 成功连接到服务器: {server_name}")
        # 可以在这里添加自定义的连接后逻辑

    async def custom_on_discover(client, server_name):
        print(f"🔍 发现新服务器: {server_name}")
        await client.initialize_mcp_server(server_name)

    try:
        print("正在使用自定义回调初始化 MCP 客户端...")

        # 使用自定义回调函数初始化
        mcp_client = await initialize_mcp_client(
            client_name="custom_client", host="localhost", wait_time=3.0
        )

        # 设置自定义回调
        mcp_client.on_mcp_server_discovered = custom_on_discover
        mcp_client.on_mcp_connect = custom_on_connect
        mcp_client.on_mcp_disconnect = on_mcp_disconnect

        print("自定义 MCP 客户端初始化成功！")

        # 等待一段时间以观察回调
        await anyio.sleep(5)

        # 关闭客户端
        await mcp_client.stop()
        print("自定义 MCP 客户端已关闭")

    except Exception as e:
        print(f"自定义使用过程中出现错误: {e}")


async def mcp_tools_integration():
    """MCP 工具集成示例"""
    try:
        print("正在初始化 MCP 客户端以集成工具...")

        mcp_client = await initialize_mcp_client(
            client_name="tools_client", host="localhost", wait_time=3.0
        )

        # 获取工具并转换为 LlamaIndex 格式
        tools = await get_mcp_tools(mcp_client, server_name="ESP32 Demo Server")

        if tools:
            print(f"成功集成 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool.metadata.name}: {tool.metadata.description}")

            # 这里可以将工具添加到你的 LlamaIndex 代理中
            # agent = AgentRunner.from_llm(llm=your_llm, tools=tools, verbose=True)

        else:
            print("未找到可用的 MCP 工具")

        await mcp_client.stop()

    except Exception as e:
        print(f"工具集成过程中出现错误: {e}")


async def main():
    """主函数 - 运行所有示例"""
    print("=" * 50)
    print("MCP 客户端使用示例")
    print("=" * 50)

    # 运行简单使用示例
    print("\n1. 简单使用示例:")
    await simple_mcp_usage()

    print("\n" + "-" * 30)

    # 运行自定义回调示例
    print("\n2. 自定义回调示例:")
    await custom_callback_mcp_usage()

    print("\n" + "-" * 30)

    # 运行工具集成示例
    print("\n3. 工具集成示例:")
    await mcp_tools_integration()

    print("\n" + "=" * 50)
    print("所有示例运行完成！")


if __name__ == "__main__":
    # 运行主函数
    anyio.run(main)
