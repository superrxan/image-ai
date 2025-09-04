import asyncio
import anyio
import time


# ===== asyncio 方式 =====
async def asyncio_worker(name: str):
    try:
        for i in range(5):
            print(f"asyncio {name}: {i}")
            await asyncio.sleep(1)
    except asyncio.CancelledError:
        print(f"asyncio {name} cancelled")
    finally:
        print(f"asyncio {name} cleanup")


async def asyncio_main():
    print("=== asyncio 方式 ===")
    # 手动创建和管理任务
    tasks = [
        asyncio.create_task(asyncio_worker("A")),
        asyncio.create_task(asyncio_worker("B")),
    ]

    try:
        # 等待所有任务完成
        await asyncio.gather(*tasks)
    except KeyboardInterrupt:
        print("asyncio: KeyboardInterrupt")
        # 手动取消所有任务
        for task in tasks:
            task.cancel()
        # 等待任务完成取消
        await asyncio.gather(*tasks, return_exceptions=True)
    print("asyncio main ended")


# ===== anyio 方式 =====
async def anyio_worker(name: str):
    try:
        for i in range(5):
            print(f"anyio {name}: {i}")
            await anyio.sleep(1)
    except anyio.get_cancelled_exc_class():
        print(f"anyio {name} cancelled")
    finally:
        print(f"anyio {name} cleanup")


async def anyio_main():
    print("=== anyio 方式 ===")
    # 使用任务组自动管理
    async with anyio.create_task_group() as tg:
        tg.start_soon(anyio_worker, "A")
        tg.start_soon(anyio_worker, "B")

        try:
            # 等待取消信号
            await anyio.sleep_forever()
        except anyio.get_cancelled_exc_class():
            print("anyio: Cancelled")
            tg.cancel_scope.cancel()
    print("anyio main ended")


if __name__ == "__main__":
    print("运行 asyncio 版本...")
    try:
        asyncio.run(asyncio_main())
    except KeyboardInterrupt:
        print("asyncio 被中断")

    print("\n" + "=" * 50 + "\n")

    print("运行 anyio 版本...")
    try:
        anyio.run(anyio_main)
    except KeyboardInterrupt:
        print("anyio 被中断")
