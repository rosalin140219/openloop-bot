import json
import random
import time


from loguru import logger
import aiohttp
from solders.keypair import Keypair

from config import timeout


class OpenLoop(object):
    def __init__(self, email, password, invited_by, proxy):
        self.email = email
        self.password = password
        self.invited_by = invited_by
        self.proxy = proxy
        self.register_url = "https://api.openloop.so/users/register"
        self.login_url = "https://api.openloop.so/users/login"
        self.profile_url = "https://api.openloop.so/users/profile"
        self.bandwidth_info_url = "https://api.openloop.so/bandwidth/info"
        self.link_wallet_url = "https://api.openloop.so/users/link-wallet"
        self.missions_url = "https://api.openloop.so/missions"
        self.complete_url = "https://api.openloop.so/missions/{}/complete"
        self.share_url = "https://api.openloop.so/bandwidth/share"

    async def register(self, name):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                payload = json.dumps({
                    "name": name,
                    "username": self.email,
                    "password": self.password,
                    "inviteCode": self.invited_by
                })
                headers = {
                    'Content-Type': 'application/json'
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.register_url, headers=headers, data=payload, proxy=self.proxy,
                                            timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.text()
                            code = json.loads(data).get('code')
                            if code == 2000:
                                logger.info(f"Account {self.email} registered successfully")
                                return True
                            else:
                                logger.error(f"Account {self.email} registered failed")
                        else:
                            logger.error(f"Account {self.email} registered failed, status code: {response.status}, "
                                         f"response: {response.text}")
            except Exception as e:
                logger.error(f"{self.email} register exception,{str(e)}")
            logger.info(f"Retrying registering for account {self.email} ({attempt + 1}/{max_retries})")
            time.sleep(2)
        logger.error(f"Account {self.email} register failed after {max_retries} attempts")
        return False

    async def login(self):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                payload = json.dumps({
                    "username": self.email,
                    "password": self.password
                })
                headers = {
                    'Content-Type': 'application/json'
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.login_url, headers=headers, data=payload, proxy=self.proxy,
                                            timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.text()
                            code = json.loads(data).get('code')
                            if code == 2000:
                                token = json.loads(data).get('data').get('accessToken')
                                self.access_token = token
                                return token
                            else:
                                logger.error(f"Account {self.email} login failed")
                        else:
                            logger.error(f"Account {self.email} login failed, status code: {response.status}")
            except Exception as e:
                logger.error(f"Account {self.email} login failed, exception: {str(e)}")

            logger.info(f"Retrying login for account {self.email} ({attempt + 1}/{max_retries})")
            time.sleep(2)
        logger.error(f"Account {self.email} login failed after {max_retries} attempts")
        return None

    async def get_profile(self):
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(self.profile_url, headers=headers, proxy=self.proxy, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.text()
                        code = json.loads(data).get('code')
                        if code == 2000:
                            return json.loads(data).get('data')
                        else:
                            logger.error(f"Account {self.email} get profile failed")
                            return None
                    else:
                        logger.error(f"Account {self.email} get profile failed, status code: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Account {self.email} get profile failed, exception: {str(e)}")
            return None

    async def connect_wallet(self, private_key, token):
        try:
            message = (
               "Please sign this message to connect your wallet to OpenLoop and verifying your ownership only."
            )
            new_account = Keypair.from_base58_string(private_key)
            public_key = str(new_account.pubkey())
            signature_str = new_account.sign_message(message.encode("utf-8"))
            payload = json.dumps({
                "message": message,
                "wallet": public_key,
                "signature": str(signature_str)
            })
            headers = {
                'Authorization': f'Bearer {token}'
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(self.link_wallet_url, headers=headers, data=payload, proxy=self.proxy,
                                        timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.text()
                        code = json.loads(data).get('code')
                        if code == 2000:
                            logger.info(f"Account:{self.email} connect wallet successfully")
                            return True
                        else:
                            logger.info(f"Account:{self.email} connect wallet failed")
                    else:
                        logger.error(f"Account:{self.email} connect wallet failed, status code: {response.status}")
                        return False
            return False
        except Exception as e:
            logger.error(f"Account:{self.email} connect wallet failed, exception: {str(e)}")
            return False

    async def query_available_tasks(self, token):
        try:
            headers = {
                'Authorization': f'Bearer {token}'
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(self.missions_url, headers=headers, proxy=self.proxy, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.text()
                        code = json.loads(data).get('code')
                        if code == 2000:
                            return json.loads(data).get('data').get('missions')
                        else:
                            logger.error(f"Account {self.email} query available tasks failed")
                            return None
                    else:
                        logger.error(f"Account {self.email} query available tasks failed, status code: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Account {self.email} query available tasks failed, exception: {str(e)}")
            return None

    async def complete(self, access_token, mission_id):
        max_retries = 3
        for attempt in range(max_retries):
            try:
                headers = {
                    'Authorization': f'Bearer {access_token}'
                }
                url = self.complete_url.format(mission_id)
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, headers=headers, proxy=self.proxy, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.text()
                            code = json.loads(data).get('code')
                            if code == 2000:
                                logger.info(f"Account:{self.email} complete mission {mission_id} successfully")
                                return True
                            else:
                                logger.info(f"Account:{self.email} complete mission {mission_id} failed")
                        else:
                            logger.info(f"Account:{self.email} complete mission {mission_id} failed")
            except Exception as e:
                logger.info(f"Account:{self.email} complete mission {mission_id} exception: {str(e)}")
            logger.info(f"Retrying complete mission {mission_id} for account {self.email} ({attempt + 1}/{max_retries})")
            time.sleep(1)
        logger.error(f"Account:{self.email} complete mission {mission_id} failed after {max_retries} attempts")
        return False

    async def share(self, token):
        try:
            headers = {
                'Authorization': f'Bearer {token}'
            }
            payload = json.dumps({
                "quality": random.randint(65, 99)
            })
            async with aiohttp.ClientSession() as session:
                async with session.post(self.share_url, headers=headers, data=payload, proxy=self.proxy,
                                        timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.text()
                        code = json.loads(data).get('code')
                        if code == 2000:
                            points = json.loads(data).get('data').get('balances').get('POINT')
                            logger.info(
                                f"Account:{self.email} share bandwidth info successfully, current points:{points}, "
                                f"today earning: {self.get_today_earning(token)}")
                            return True
                        else:
                            data = await response.text()
                            logger.error(f"Account:{self.email} share bandwidth info failed， response: {data}")
                    else:
                        data = await response.text()
                        logger.error(f"Account:{self.email} share bandwidth info failed, status code: "
                                     f"{response.status}, response: {data}")
        except Exception as e:
            logger.error(f"Account:{self.email} share bandwidth info exception: {str(e)}")
        return False

    async def get_today_earning(self, token):
        try:
            headers = {
                'Authorization': f'Bearer {token}'
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(self.bandwidth_info_url, headers=headers, proxy=self.proxy, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.text()
                        code = json.loads(data).get('code')
                        if code == 2000:
                            return json.loads(data).get('data').get('todayEarning')
                        else:
                            logger.error(f"Account {self.email} get bandwidth info failed")
                            return 0
                    else:
                        logger.error(f"Account {self.email} get bandwidth info failed, status code: {response.status}")
                        return 0
        except Exception as e:
            logger.error(f"Account {self.email} get bandwidth info failed, exception: {str(e)}")
            return 0
