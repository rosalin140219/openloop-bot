import asyncio
from datetime import datetime, timedelta
import time

import aiosqlite
from api import OpenLoop
from loguru import logger
from init import update_token, fetch_tasks, update_task_executed_time, complete_task


async def execute_task(target_task, token, client):
    id, task_name, last_executed = target_task
    if task_name == 'run_share_task':
        try:
            if last_executed and datetime.now() - datetime.strptime(last_executed, '%Y-%m-%d %H:%M:%S.%f') < timedelta(
                    minutes=3):
                logger.warning(f"Skipping task {task_name} for account {client.email}")
                return
            await share_bandwidth_info(token, client)
            # 更新任务时间
            update_task_executed_time(client.email, datetime.now())
        except Exception as e:
            logger.error(f"Account:{client.email} run share task exception,{str(e)}")
    elif task_name == 'run_complete_task':
        try:
            if last_executed and datetime.now() - datetime.strptime(last_executed, '%Y-%m-%d %H:%M:%S.%f') < timedelta(
                    hours=24):
                logger.warning(f"Skipping task {task_name} for account {client.email}")
                return
            await complete_task(token, client)
            # 更新任务时间
            update_task_executed_time(client.email, datetime.now())
        except Exception as e:
            logger.error(f"Account:{client.email} complete task exception,{str(e)}")


async def share_bandwidth_info(token, client):
    if token is None:
        token = await client.login()
        if token is None:
            logger.error(f"Account:{client.email} login failed")
            return
        update_token(client.email, token)
    await client.share(token)


async def run_batch(accounts):
    tasks = []
    for account in accounts:
        client = OpenLoop(account[0], account[1], None, account[2])
        target_task = await fetch_tasks(account[0])
        for target in target_task:
            # tasks.append(share_bandwidth_info(account[3], client))
            tasks.append(execute_task(target, account[3], client))
    await asyncio.gather(*tasks)


async def fetch_farm_accounts(limit=10, offset=0):
    async with aiosqlite.connect("openloop.db") as db:
        async with db.execute('SELECT email, password, proxy, token FROM accounts where registered = TRUE order by id asc LIMIT ? OFFSET ? ', (limit, offset)) as cursor:
            accounts = await cursor.fetchall()
    return accounts


async def run_farm(batch_size=10):
    while True:
        start_time = time.time()  # 获取开始时间
        async with aiosqlite.connect("openloop.db") as db:
            async with db.execute('SELECT COUNT(*) FROM accounts') as cursor:
                total_accounts = await cursor.fetchone()
                total_account = total_accounts[0]

        for offset in range(0, total_account, batch_size):
            accounts = await fetch_farm_accounts(limit=batch_size, offset=offset)
            await run_batch(accounts)
        end_time = time.time()  # 获取结束时间
        logger.info(f"一次任务执行的时间: {end_time - start_time}")
        # await asyncio.sleep(30)
