import asyncio
import sqlite3
import sys
import time
from datetime import datetime

import aiosqlite
from loguru import logger
from solders.keypair import Keypair

from account import Account
from config import password
from config import proxy_mode
import api

def create_tables():
    conn = sqlite3.connect('openloop.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NULL,
        email TEXT NOT NULL,
        password TEXT NOT NULL,
        invited_by TEXT NULL,
        invite_code TEXT NULL,
        registered BOOLEAN DEFAULT FALSE,
        token TEXT NULL,
        address TEXT NULL,
        private_key TEXT NULL,
        wallet_linked BOOLEAN DEFAULT FALSE,
        proxy TEXT NULL
    )
    ''')

    cursor.execute('''
       CREATE TABLE IF NOT EXISTS task (
           id INTEGER PRIMARY KEY AUTOINCREMENT,
           email TEXT NOT NULL,
           task_name TEXT NOT NULL,
           last_executed TIMESTAMP
       )
       ''')
    conn.commit()
    conn.close()


def insert_account(accounts):
    # 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
    conn = sqlite3.connect('openloop.db')
    # 创建一个游标对象
    cursor = conn.cursor()
    try:
        cursor.executemany('''
                INSERT INTO accounts (email, password, invited_by, proxy)
                VALUES (?, ?, ?, ?)
            ''', accounts)
        # 提交事务
        conn.commit()
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()


def insert_proxies(email, proxies):
    # 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
    conn = sqlite3.connect('openloop.db')
    # 创建一个游标对象
    cursor = conn.cursor()
    try:
        # 创建包含 email 和 proxy 的元组列表
        proxy_data = [(email, proxy) for proxy in proxies]
        cursor.executemany('''
            INSERT INTO proxy (email, proxy, status)
            VALUES (?, ?, 'OK')
        ''', proxy_data)
        # 提交事务
        conn.commit()
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()


def update_wallet_info(address, private_key, wallet_linked, token, email):
    conn = sqlite3.connect('openloop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE accounts SET address = ?, private_key = ?, wallet_linked = ?, token = ?
            WHERE email = ?
            ''', (address, private_key, wallet_linked, token, email))
        conn.commit()
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()


def update_register_info(email, name, registered):
    conn = sqlite3.connect('openloop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE accounts SET name = ?, registered = ? WHERE email = ?
            ''', (name, registered, email))
        conn.commit()
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()

def update_token(email, token):
    conn = sqlite3.connect('openloop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE accounts SET token = ? WHERE email = ?
            ''', (token, email))
        conn.commit()
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()

def insert_task(email, tasks):
    # 连接到 SQLite 数据库（如果数据库不存在，则会自动创建）
    conn = sqlite3.connect('openloop.db')
    # 创建一个游标对象
    cursor = conn.cursor()
    try:
        # 创建包含 email 和 proxy 的元组列表
        task_data = [(email, task) for task in tasks]
        cursor.executemany('''
            INSERT INTO task (email, task_name, last_executed)
            VALUES (?, ?, NULL)
        ''', task_data)
        # 提交事务
        conn.commit()
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()


async def fetch_tasks(email):
    async with aiosqlite.connect('openloop.db') as db:
        async with db.execute('SELECT id, task_name, last_executed FROM task WHERE email = ?', (email,)) as cursor:
            tasks = await cursor.fetchall()
    return tasks


def update_task_executed_time(email, now):
    conn = sqlite3.connect('openloop.db')
    cursor = conn.cursor()
    try:
        cursor.execute('''
            UPDATE task SET last_executed = ? WHERE email = ?
            ''', (now, email))
        conn.commit()
    finally:
        # 关闭游标和连接
        cursor.close()
        conn.close()


def init():
    # 创建表
    create_tables()
    # 读取代理
    proxies = []
    with open('proxies.txt', 'r') as file:
        for line in file:
            line = line.strip()
            proxies.append(line)
    if proxy_mode and len(proxies) == 0:
        logger.error("请配置代理proxies.txt")
        sys.exit(0)
    accounts = []
    with open('accounts.txt', 'r') as file:
        for line in file:
            line = line.strip().split(":")
            name = line[0].split("@")[0]
            account = Account(name, line[0], password, line[1], None)
            accounts.append(account)
    if proxy_mode:
        if len(proxies) < len(accounts):
            logger.error("代理的数量小于账户的数量，请重新配置，确保代理数量大于等于账户的数量")
            sys.exit(0)
        for account in accounts:
            account.proxy = proxies.pop()
    # 插入数据
    insert_accounts = [(account.email, account.password, account.invited_by, account.proxy) for account in accounts]
    insert_account(insert_accounts)
    # 保存任务数据
    tasks = ['run_complete_task', 'run_share_task']
    for account in accounts:
        insert_task(account.email, tasks)



async def link_wallet():
    max_retries = 5
    for _ in range(max_retries):
        conn = sqlite3.connect('openloop.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT email, password, invited_by, proxy, token FROM accounts WHERE wallet_linked = FALSE and registered = TRUE
            ''')
        accounts = cursor.fetchall()
        conn.close()
        if len(accounts) == 0:
            logger.info("所有账户都已经连接钱包，退出")
            break
        for account in accounts:
            try:
                client = api.OpenLoop(account[0], account[1], account[2], account[3])
                token = account[4]
                if token is None:
                    logger.error(f"Account{account[0]} token is None, now trying to login......")
                    token = await client.login()
                    if token is None:
                        logger.error(f"Account{account[0]} login failed")
                        continue
                new_account = Keypair()
                # 获取公钥和私钥
                public_key = str(new_account.pubkey())
                private_key = str(new_account)
                connected = await client.connect_wallet(private_key, token)
                # address, private_key, wallet_linked, token, email
                update_wallet_info(public_key, private_key, connected, token,  account[0])
            except Exception as e:
                logger.error(f"Account{account[0]} link wallet exception,{e}")
            time.sleep(1)


async def register():
    max_retries = 5
    for _ in range(max_retries):
        conn = sqlite3.connect('openloop.db')
        cursor = conn.cursor()
        cursor.execute('''
               SELECT email, password, invited_by, proxy FROM accounts WHERE registered = FALSE
               ''')
        accounts = cursor.fetchall()
        conn.close()
        if len(accounts) == 0:
            logger.info("所有账户都已经完成注册，退出")
            break
        for account in accounts:
            try:
                client = api.OpenLoop(account[0], account[1], account[2], account[3])
                name = account[0].split("@")[0]
                registered = await client.register(name)
                update_register_info(account[0], name, registered)
            except Exception as e:
                logger.error(f"Account{account[0]} link wallet exception,{e}")
            time.sleep(1)


async def complete_task(token, client):
    if token is None:
        token = await client.login()
        if token is None:
            logger.error(f"Account:{client.email} login failed")
            return
        update_token(client.email, token)
    missions = await client.query_available_tasks(token)
    if missions is None or len(missions) == 0:
        logger.info(f"Account:{client.email} has no available tasks")
        return
    for mission in missions:
        mission_id = mission['missionId']
        status = mission['status']
        if status != 'available':
            continue
        await client.complete(token, mission_id)


async def run_batch(accounts):
    tasks = []
    for account in accounts:
        client = api.OpenLoop(account[0], account[1], None, account[2])
        tasks.append(complete_task(account[3], client))
    await asyncio.gather(*tasks)


async def fetch_accounts(limit=10, offset=0):
    async with aiosqlite.connect("openloop.db") as db:
        async with db.execute('SELECT email, password, proxy, token FROM accounts where registered = TRUE LIMIT ? OFFSET ?', (limit, offset)) as cursor:
            accounts = await cursor.fetchall()
    return accounts


async def run_complete_task(batch_size=10):
    async with aiosqlite.connect("openloop.db") as db:
        async with db.execute('SELECT COUNT(*) FROM accounts') as cursor:
            total_accounts = await cursor.fetchone()
            total_account = total_accounts[0]

    for offset in range(0, total_account, batch_size):
        accounts = await fetch_accounts(limit=batch_size, offset=offset)
        await run_batch(accounts)







