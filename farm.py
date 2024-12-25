import asyncio
import time

import aiosqlite
from api import OpenLoop
from loguru import logger
from init import update_token


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
        tasks.append(share_bandwidth_info(account[3], client))
    await asyncio.gather(*tasks)


async def fetch_farm_accounts(limit=10, offset=0):
    async with aiosqlite.connect("openloop.db") as db:
        async with db.execute('SELECT email, password, proxy, token FROM accounts where registered = TRUE LIMIT ? OFFSET ? order by id asc', (limit, offset)) as cursor:
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
        diff = 180 - (end_time - start_time)
        logger.info(f"一次任务执行的时间: {end_time - start_time}, sleep {diff} seconds")
        if diff > 0:
            time.sleep(diff)
