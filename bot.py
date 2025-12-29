from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout,
    BasicAuth
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from eth_account import Account
from eth_account.messages import encode_defunct
from eth_utils import to_hex
from web3 import Web3
from datetime import datetime
from colorama import *
import asyncio, json, re, os, pytz, random

wib = pytz.timezone('Asia/Jakarta')

class X1:
    def __init__(self) -> None:
        self.BASE_API = "https://tapi.kod.af"
        self.RPC_URL = "https://maculatus-rpc.x1eco.com"
        self.CHAIN_ID = 10778
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
            {Fore.GREEN + Style.BRIGHT}        █████╗ ██████╗ ██████╗     ███╗   ██╗ ██████╗ ██████╗ ███████╗
            {Fore.GREEN + Style.BRIGHT}       ██╔══██╗██╔══██╗██╔══██╗    ████╗  ██║██╔═══██╗██╔══██╗██╔════╝
            {Fore.GREEN + Style.BRIGHT}       ███████║██║  ██║██████╔╝    ██╔██╗ ██║██║   ██║██║  ██║█████╗  
            {Fore.GREEN + Style.BRIGHT}       ██╔══██║██║  ██║██╔══██╗    ██║╚██╗██║██║   ██║██║  ██║██╔══╝  
            {Fore.GREEN + Style.BRIGHT}       ██║  ██║██████╔╝██████╔╝    ██║ ╚████║╚██████╔╝██████╔╝███████╗
            {Fore.GREEN + Style.BRIGHT}       ╚═╝  ╚═╝╚═════╝ ╚═════╝     ╚═╝  ╚═══╝ ╚═════╝ ╚═════╝ ╚══════╝
            {Fore.YELLOW + Style.BRIGHT}       Modified by ADB NODE (Auto TX & Skip Error)
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    async def send_daily_tx(self, private_key, address):
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        if not web3.is_connected():
            self.log(f"{Fore.RED}RPC Connection Failed! Skipping TX...{Style.RESET_ALL}")
            return False
        try:
            random_acc = web3.eth.account.create()
            to_address = random_acc.address
            amount = random.uniform(0.1, 0.5)
            value = web3.to_wei(amount, 'ether')
            nonce = web3.eth.get_transaction_count(address)
            tx = {
                'nonce': nonce,
                'to': to_address,
                'value': value,
                'gas': 21000,
                'gasPrice': web3.eth.gas_price,
                'chainId': self.CHAIN_ID
            }
            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.log(f"{Fore.GREEN}Daily TX Sent! Hash: {web3.to_hex(tx_hash)[:20]}...{Style.RESET_ALL}")
            return True
        except Exception as e:
            self.log(f"{Fore.RED}Daily TX Error: {str(e)}{Style.RESET_ALL}")
            return False

    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename): return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
        except: self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes): return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if not self.proxies: return None
        if account not in self.account_proxies:
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def build_proxy_config(self, proxy=None):
        if not proxy: return None, None, None
        if proxy.startswith("socks"):
            return ProxyConnector.from_url(proxy), None, None
        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                u, p, hp = match.groups()
                return None, f"http://{hp}", BasicAuth(u, p)
            return None, proxy, None
        return None, None, None

    async def auth_signin(self, address: str, signature: str, proxy_url=None):
        url = f"{self.BASE_API}/signin"
        data = json.dumps({"signature": signature})
        headers = {**self.HEADERS[address], "Content-Type": "application/json"}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.post(url, headers=headers, data=data, proxy=proxy, proxy_auth=auth) as res:
                    res.raise_for_status()
                    return await res.json()
        except: return None

    async def user_data(self, address: str, proxy_url=None):
        url = f"{self.BASE_API}/me"
        headers = {**self.HEADERS[address], "Authorization": self.access_tokens.get(address, "")}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url, headers=headers, proxy=proxy, proxy_auth=auth) as res:
                    res.raise_for_status()
                    return await res.json()
        except: return None

    async def request_faucet(self, address: str, proxy_url=None):
        url = f"https://nft-api.x1.one/testnet/faucet"
        params = {"address": address}
        headers = {**self.HEADERS[address], "Authorization": self.access_tokens.get(address, "")}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=20)) as session:
                async with session.get(url, headers=headers, params=params, proxy=proxy, proxy_auth=auth) as res:
                    if res.status == 429:
                        self.log(f"{Fore.YELLOW}Faucet Rate Limit (429). Skipping...{Style.RESET_ALL}")
                        return None
                    if "application/json" in res.headers.get("Content-Type", ""):
                        return await res.json()
                    return None
        except Exception: return None

    async def quest_list(self, address: str, proxy_url=None):
        url = f"{self.BASE_API}/quests"
        headers = {**self.HEADERS[address], "Authorization": self.access_tokens.get(address, "")}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=30)) as session:
                async with session.get(url, headers=headers, proxy=proxy, proxy_auth=auth) as res:
                    res.raise_for_status()
                    return await res.json()
        except: return None

    async def claim_quest(self, address: str, q_id: str, title: str, proxy_url=None):
        url = f"{self.BASE_API}/quests"
        params = {"quest_id": q_id}
        headers = {**self.HEADERS[address], "Authorization": self.access_tokens.get(address, ""), "Content-Length": "0"}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector) as session:
                async with session.post(url, headers=headers, params=params, proxy=proxy, proxy_auth=auth) as res:
                    if res.status == 200:
                        self.log(f"{Fore.GREEN} ● {title} Completed{Style.RESET_ALL}")
                        return True
                    return False
        except: return False

    async def process_accounts(self, account: str, address: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        
        # Signin
        msg = encode_defunct(text="X1 Testnet Auth")
        sig = to_hex(Account.sign_message(msg, private_key=account).signature)
        signin = await self.auth_signin(address, sig, proxy)
        
        if signin and "token" in signin:
            self.access_tokens[address] = signin["token"]
            self.log(f"{Fore.GREEN}Login Success{Style.RESET_ALL}")
            
            # Point Info
            user = await self.user_data(address, proxy)
            if user: self.log(f"Current Points: {user.get('points')}")

            # Faucet (Error handler included inside)
            self.log("Requesting Faucet...")
            await self.request_faucet(address, proxy)
            
            # Quests
            quests = await self.quest_list(address, proxy)
            if quests:
                for q in quests:
                    title, q_id = q.get("title"), q.get("id")
                    is_done_today = q.get("is_completed_today")
                    is_done_once = q.get("is_completed")

                    if title == "Send X1T" and not is_done_today:
                        self.log("Performing Daily TX...")
                        if await self.send_daily_tx(account, address):
                            await asyncio.sleep(5)
                            await self.claim_quest(address, q_id, title, proxy)
                    elif not is_done_today and not is_done_once:
                        await self.claim_quest(address, q_id, title, proxy)
        else:
            self.log(f"{Fore.RED}Login Failed!{Style.RESET_ALL}")

    async def main(self):
        self.clear_terminal(); self.welcome()
        try:
            with open('accounts.txt', 'r') as f:
                accounts = [line.strip() for line in f if line.strip()]
        except: self.log("accounts.txt not found!"); return

        print("1. Run With Proxy\n2. Run Without Proxy")
        use_p = input("Choose [1/2]: ").strip() == "1"
        if use_p: await self.load_proxies()

        while True:
            for acc in accounts:
                addr = Account.from_key(acc).address
                self.log(f"{Fore.YELLOW}Processing: {addr[:6]}...{addr[-6:]}{Style.RESET_ALL}")
                self.HEADERS[addr] = {"User-Agent": FakeUserAgent().random, "Origin": "https://testnet.x1ecochain.com"}
                
                # အကောင့်တစ်ခုချင်းစီကို try-except နဲ့ အုပ်ထားလို့ error တက်ရင် နောက်တစ်ခုကို ဆက်သွားမယ်
                try:
                    await self.process_accounts(acc, addr, use_p)
                except Exception as e:
                    self.log(f"{Fore.RED}Error on account {addr}: {e}{Style.RESET_ALL}")
                
                # အကောင့်တစ်ခုနဲ့တစ်ခုကြား ခဏစောင့်ပေးခြင်း (429 ရှောင်ရန်)
                await asyncio.sleep(random.randint(5, 10))

            self.log("All accounts finished. Waiting 24h...")
            await asyncio.sleep(86400)

if __name__ == "__main__":
    asyncio.run(X1().main())
