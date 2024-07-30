from typing import Optional, Union
import random
import asyncio

from web3 import Web3

import config
from config import logger
from py_okx_async.OKXClient import OKXClient
from py_okx_async.asset.models import TransferTypes, Currency
from py_okx_async.models import OKXCredentials, AccountTypes

class OKXActions:
    def __init__(self, credentials: OKXCredentials):
        self.entrypoint_url = 'https://www.okx.com'
        self.credentials = credentials
        self.okx_client = None
        if self.credentials.completely_filled():
            self.okx_client = OKXClient(credentials=credentials, entrypoint_url=self.entrypoint_url)


    async def all_balances_are_zero(self, token_symbol: str, amount: float = 0.0) -> bool:
        for subaccount_name in await self.okx_client.subaccount.list():
            balances = await self.okx_client.subaccount.asset_balances(subAcct=subaccount_name, token_symbol=token_symbol)
            for balance in balances.values():
                if balance.availBal > amount:
                    return False
        return True

    async def collect_funds_from_subaccounts(self, token_symbol:str = "ETH"):
        token_symbol=token_symbol.upper()
        if not await self.all_balances_are_zero(token_symbol=token_symbol):
            accs=[]
            for subaccount_name in await self.okx_client.subaccount.list():
                balances = await self.okx_client.subaccount.asset_balances(subAcct=subaccount_name, token_symbol=token_symbol)
                for balance in balances.values():
                    avail_bal = balance.availBal
                    if avail_bal > 0.0:
                        try:
                            await self.okx_client.asset.transfer(
                                token_symbol='ETH', amount=avail_bal, to_=AccountTypes.Funding, subAcct=subaccount_name,
                                type=TransferTypes.SubToMasterMasterKey
                            )
                        except Exception as e:
                            logger.error(f'cannot withdraw from acc {subaccount_name}, {e}')
                        accs.append(subaccount_name)
            logger.info(f' {token_symbol}  moved from subaccounts {accs} ')
        logger.info(f'no balances on subaccounts')

    async def get_withdrawal_fee(self, token_symbol: str, chain: str) -> Optional[float]:

        token_symbol = token_symbol.upper()
        currencies = await self.okx_client.asset.currencies(token_symbol=token_symbol)
        if token_symbol not in currencies:
            return None

        currency = currencies[token_symbol]
        if chain not in currency:
            return None


        currency_info: Currency = currency[chain]
        if not currency_info.canWd:
            return None

        if currency_info.minFee:
            return currency_info.minFee
        return None

    async def try_to_get_tx_hash(self, wd_id: Union[str, int]) -> str:
        wd_id = int(wd_id)
        withdrawal_history = await self.okx_client.asset.withdrawal_history(wdId=wd_id)
        while not withdrawal_history.get(wd_id).txId:
            await asyncio.sleep(10)
            withdrawal_history = await self.okx_client.asset.withdrawal_history(wdId=wd_id)
        logger.success(f'successful withdrawal, tx: {withdrawal_history.get(wd_id).txId}')

    async def withdraw(
            self,
            to_address: str,
            amount: float | int | str,
            token_symbol: str,
            chain: str,
    ) -> str:
        failed_text = 'Failed to withdraw from OKX'
        to_address= Web3.to_checksum_address(to_address)
        token_symbol = token_symbol.upper()
        try:
            if not self.okx_client:
                return f'{failed_text}: there is no okx_client'

            fee = await self.get_withdrawal_fee(token_symbol=token_symbol, chain=chain)
            if not fee:
                return f'{failed_text} | can not get fee for withdraw'

            withdrawal_token = await self.okx_client.asset.withdrawal(
                token_symbol=token_symbol, amount=amount, toAddr=to_address, fee=fee, chain=chain
            )
            withdrawal_id = withdrawal_token.wdId
            if withdrawal_id:
                logger.info(f'withdrawal request sent: {withdrawal_id}, wallet: {to_address}, token, chain: {token_symbol, chain}, amount: {amount}')
                return withdrawal_id


            return f'{failed_text}! withdrawal_id: {withdrawal_id}'

        except BaseException as e:
            logger.exception(f'withdraw: {e}')
            return f'{failed_text}: {e}'

    @staticmethod
    async def randfloat(from_: float, to_: float, decimal_places: int = 5) -> float:
        return int((random.uniform(from_, to_) * 10 ** decimal_places)) / 10 ** decimal_places


    @staticmethod
    async def get_wallet_addresses(path: str) -> list[str]:
        wallet_addresses = []
        with open(path) as f:
            for wallet_address in f:
                wallet_addresses.append(wallet_address.strip())
        return wallet_addresses


    @staticmethod
    async def check_gas_price(max_gas_price: int | float = 1000, sleep: int = 60, endpoint: str | None = None):
        if endpoint:
            w3 = Web3(provider=Web3.HTTPProvider(endpoint_uri=endpoint))
            if not w3.is_connected():
                logger.error(f'ethereum rpc does not work')
            gas_price = w3.eth.gas_price
            while float(w3.from_wei(gas_price, unit='gwei')) > max_gas_price:
                logger.info(f'current gas is too high {w3.from_wei(gas_price, unit="gwei")} > {max_gas_price}')
                await asyncio.sleep(sleep)
                gas_price = w3.eth.gas_price
            logger.info(f'gas price {w3.from_wei(gas_price, unit="gwei")} is good')
        else:
            logger.warning(f'no GWEI control')

