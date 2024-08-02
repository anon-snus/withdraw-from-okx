import os
import sys
from pathlib import Path
from loguru import logger
from py_okx_async.models import OKXCredentials

okx_api_key = ''
okx_secret_key = ''
okx_passphrase = ''


proxy = '' # leave blank if u do not want to use proxy, format type (socks5/http)://login:password@ip:port example: socks5://WvCkB:tzXp86@122.12.145.138:64552

maximum_gas_price = 100
withdraw_from_subaccounts = True # True/False
shuffle_wallets = True #True / false
ethereum_rpc='https://rpc.mevblocker.io'

'''
all correct tokens and networks in supporting_tokens (also u can use currincies function to see them up to date) 
'''
# asset
token_name='ETH'

random_chains = True # True / False if True will randomly choose one chain from list_random else will use chain in chain tp withdraw
chain_to_withdraw='Arbitrum One'
list_random = ['Arbitrum One', 'Zksync era', 'Linea']

withdraw_amount = {'from': 0.001, 'to': 0.002, 'decimal_places': 5}
delay_between_withdrawals = {'from': 100, 'to': 500}



################################
# do not touch
################################
okx_credentials = OKXCredentials(
    api_key=okx_api_key,
    secret_key=okx_secret_key,
    passphrase=okx_passphrase
)

if getattr(sys, 'frozen', False):
    ROOT_DIR = Path(sys.executable).parent.absolute()
else:
    ROOT_DIR = Path(__file__).parent.parent.absolute()

ADDRESSES_PATH = os.path.join(ROOT_DIR, 'withdrawal/wallets.txt')
LOGS_DIR = os.path.join(ROOT_DIR, 'withdrawal/logs')

logger.add(
    f'{os.path.join(LOGS_DIR, "debug.log")}',
    format='{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}',
    level='INFO'
)
