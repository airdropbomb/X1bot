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
from web3 import Web3  # Web3 ထည့်သွင်းခြင်း
from datetime import datetime
from colorama import *
import asyncio, json, re, os, pytz, random

wib = pytz.timezone('Asia/Jakarta')

class X1:
    def __init__(self) -> None:
        self.BASE_API = "https://tapi.kod.af"
        self.RPC_URL = "https://maculatus-rpc.x1eco.com" # X1 Testnet RPC
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
            {Fore.YELLOW + Style.BRIGHT}       Modified by ADB NODE & Daily TX Added
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"

    async def send_daily_tx(self, private_key, address):
        """အခြား Random Address တစ်ခုဆီသို့ TX ပို့ခြင်း"""
        web3 = Web3(Web3.HTTPProvider(self.RPC_URL))
        if not web3.is_connected():
            self.log(f"{Fore.RED}RPC Connection Failed!{Style.RESET_ALL}")
            return False

        try:
            # Random Receiver Address တည်ဆောက်ခြင်း
            random_acc = web3.eth.account.create()
            to_address = random_acc.address
            
            # ပို့မည့်ပမာဏ (0.1 မှ 0.5 အကြား random)
            amount = random.uniform(0.1, 0.5)
            value = web3.to_wei(amount, 'ether')

            nonce = web3.eth.get_transaction_count(address)
            gas_price = web3.eth.gas_price

            tx = {
                'nonce': nonce,
                'to': to_address,
                'value': value,
                'gas': 21000,
                'gasPrice': gas_price,
                'chainId': self.CHAIN_ID
            }

            signed_tx = web3.eth.account.sign_transaction(tx, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}TX Sent  :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Successfully! Hash: {web3.to_hex(tx_hash)[:20]}...{Style.RESET_ALL}"
            )
            return True
        except Exception as e:
            self.log(f"{Fore.RED}TX Error: {str(e)}{Style.RESET_ALL}")
            return False

    # ... (ကျန်တဲ့ load_proxies, build_proxy_config စတဲ့ function များ မူရင်းအတိုင်းထားသည်)
    async def load_proxies(self):
        filename = "proxy.txt"
        try:
            if not os.path.exists(filename):
                return
            with open(filename, 'r') as f:
                self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
        except: self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes): return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, account):
        if account not in self.account_proxies:
            if not self.proxies: return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[account] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[account]

    def build_proxy_config(self, proxy=None):
        if not proxy: return None, None, None
        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None
        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                return None, f"http://{host_port}", BasicAuth(username, password)
            else: return None, proxy, None
        return None, None, None

    def generate_address(self, account: str):
        try: return Account.from_key(account).address
        except: return None

    def generate_signature(self, account: str):
        message = encode_defunct(text="X1 Testnet Auth")
        return to_hex(Account.sign_message(message, private_key=account).signature)

    def mask_account(self, account):
        return account[:6] + '*' * 6 + account[-6:]

    def print_question(self):
        print(f"{Fore.WHITE}1. Run With Proxy\n2. Run Without Proxy")
        choice = input("Choose [1/2] -> ").strip()
        return int(choice), True

    async def auth_signin(self, address: str, signature: str, proxy_url=None):
        url = f"{self.BASE_API}/signin"
        data = json.dumps({"signature": signature})
        headers = {**self.HEADERS[address], "Content-Type": "application/json"}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        async with ClientSession(connector=connector) as session:
            async with session.post(url, headers=headers, data=data, proxy=proxy, proxy_auth=auth) as res:
                return await res.json()

    async def user_data(self, address: str, proxy_url=None):
        url = f"{self.BASE_API}/me"
        headers = {**self.HEADERS[address], "Authorization": self.access_tokens[address]}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        async with ClientSession(connector=connector) as session:
            async with session.get(url, headers=headers, proxy=proxy, proxy_auth=auth) as res:
                return await res.json()

    async def request_faucet(self, address: str, proxy_url=None):
        url = f"https://nft-api.x1.one/testnet/faucet"
        params = {"address": address}
        headers = {**self.HEADERS[address], "Authorization": self.access_tokens[address]}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        async with ClientSession(connector=connector) as session:
            async with session.get(url, headers=headers, params=params, proxy=proxy, proxy_auth=auth) as res:
                if res.status == 500: return None
                return await res.json()

    async def quest_list(self, address: str, proxy_url=None):
        url = f"{self.BASE_API}/quests"
        headers = {**self.HEADERS[address], "Authorization": self.access_tokens[address]}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        async with ClientSession(connector=connector) as session:
            async with session.get(url, headers=headers, proxy=proxy, proxy_auth=auth) as res:
                return await res.json()

    async def claim_quest(self, address: str, quest_id: str, title: str, proxy_url=None):
        url = f"{self.BASE_API}/quests"
        params = {"quest_id": quest_id}
        headers = {**self.HEADERS[address], "Authorization": self.access_tokens[address], "Content-Length": "0"}
        connector, proxy, auth = self.build_proxy_config(proxy_url)
        async with ClientSession(connector=connector) as session:
            async with session.post(url, headers=headers, params=params, proxy=proxy, proxy_auth=auth) as res:
                if res.status == 200: return await res.json()
                return None

    async def process_accounts(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        signature = self.generate_signature(account)
        signin = await self.auth_signin(address, signature, proxy)
        
        if signin and "token" in signin:
            self.access_tokens[address] = signin["token"]
            self.log(f"{Fore.GREEN}Login Success{Style.RESET_ALL}")
            
            user = await self.user_data(address, proxy)
            if user: self.log(f"Points: {user.get('points')}")

            # 1. Faucet တောင်းခြင်း
            await self.request_faucet(address, proxy)
            
            # 2. Quest စာရင်းယူခြင်း
            quests = await self.quest_list(address, proxy)
            if quests:
                for quest in quests:
                    title = quest.get("title")
                    q_id = quest.get("id")
                    
                    # Daily TX Quest ဖြစ်လျှင် အရင်ဆုံး တကယ်လွှဲမည်
                    if title == "Send X1T" and not quest.get("is_completed_today"):
                        self.log(f"Starting Daily TX for '{title}'...")
                        tx_done = await self.send_daily_tx(account, address)
                        if tx_done:
                            await asyncio.sleep(5) # TX confirm ဖြစ်အောင် ခေတ္တစောင့်ခြင်း
                            await self.claim_quest(address, q_id, title, proxy)
                    
                    # ကျန်သော Quest များကို Claim ခြင်း
                    elif not quest.get("is_completed_today") and not quest.get("is_completed"):
                        claim = await self.claim_quest(address, q_id, title, proxy)
                        if claim: self.log(f"{Fore.GREEN} ● {title} Completed{Style.RESET_ALL}")

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            proxy_choice, rotate_proxy = self.print_question()
            while True:
                self.clear_terminal(); self.welcome()
                self.log(f"Accounts Total: {len(accounts)}")
                if proxy_choice == 1: await self.load_proxies()
                for acc in accounts:
                    addr = self.generate_address(acc)
                    if addr:
                        self.log(f"Processing: {self.mask_account(addr)}")
                        self.HEADERS[addr] = {"User-Agent": FakeUserAgent().random, "Origin": "https://testnet.x1ecochain.com"}
                        await self.process_accounts(acc, addr, proxy_choice == 1, rotate_proxy)
                
                self.log("All accounts processed. Sleeping 24h...")
                await asyncio.sleep(86400)
        except Exception as e: self.log(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(X1().main())
