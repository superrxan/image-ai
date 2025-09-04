import anyio


async def task_a():
    print("A: start")
    await anyio.sleep(1)
    print("A: about to raise")
    raise RuntimeError("A failed")  # A 异常退出


async def task_b():
    print("B: start")
    try:
        while True:
            print("B: working...")
            await anyio.sleep(0.5)
    except anyio.get_cancelled_exc_class():
        print("B: cancelled")
    finally:
        print("B: cleanup")


async def main():
    try:
        async with anyio.create_task_group() as tg:
            tg.start_soon(task_a)
            tg.start_soon(task_b)
    except Exception as e:
        print(f"main caught: {e!r}")


if __name__ == "__main__":
    anyio.run(main)
