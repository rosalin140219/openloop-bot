import argparse
import asyncio

from loguru import logger
from init import init, register, link_wallet, run_complete_task
from farm import run_farm


async def main():
    logger.info("Openloop Bot启动")

    parser = argparse.ArgumentParser(description="根据命令执行不同的脚本")
    parser.add_argument("command", type=str, help="""
                    支持如下命令运行: \r\n
                        init : 执行初始胡
                        farm: 执行跑积分脚本 \r\n
                """)

    # 解析命令行参数
    args = parser.parse_args()
    if args.command == "init":
        # 注册流程
        init()
    elif args.command == "register":
        await register()
    elif args.command == "link_wallet":
        await link_wallet()
    elif args.command == "complete_task":
        await run_complete_task()
    elif args.command == "farm":
        await run_farm(batch_size=10)
    else:
        logger.error(f"未知命令: {args.command}")
    pass

if __name__ == '__main__':
    asyncio.run(main())
