import asyncio
import random

from config import logger
from tqdm.asyncio import tqdm

import currencies
from okx_actions import OKXActions
import config
from proxy import check_proxy


async def main():

	if await check_proxy(proxy=config.proxy):
		okx_actions = OKXActions(credentials=config.okx_credentials, proxy=config.proxy)
		wallets = await okx_actions.get_wallet_addresses(config.ADDRESSES_PATH)

		if config.withdraw_from_subaccounts:
			logger.info(f'starting withdraw from sub accounts')
			await okx_actions.collect_funds_from_subaccounts(token_symbol=config.token_name.upper())

		if config.shuffle_wallets:
			random.shuffle(wallets)

		for num, wallet in enumerate(wallets, start=1):
			await okx_actions.check_gas_price(max_gas_price=config.maximum_gas_price, endpoint=config.ethereum_rpc)
			amount=await okx_actions.randfloat(
				from_=config.withdraw_amount['from'],
	            to_=config.withdraw_amount['to'],
	            decimal_places=config.withdraw_amount['decimal_places']
			)

			network = await currencies.curr(dict=True, proxy=config.proxy)
			chain = (random.choice(config.chain_to_withdraw)).upper()
			chain = network[chain]

			try:
				id =await okx_actions.withdraw(to_address=wallet, amount=amount, token_symbol=config.token_name.upper(), chain=chain)
				await okx_actions.try_to_get_tx_hash(wd_id=id)

			except Exception as e:
				logger.error(f'cannot withdraw to {wallet}, {e}')

			sleep = (random.randint(config.delay_between_withdrawals['from'], config.delay_between_withdrawals['to']))
			logger.info(f'sleeping for {sleep}')
			progress_bar = tqdm(total=sleep, desc="Sleeping", unit="s", leave=False)
			for _ in range(sleep):
				await asyncio.sleep(1)
				progress_bar.update(1)
			progress_bar.close()
			logger.info('Awake now!')




if __name__=='__main__':
	if config.okx_credentials.completely_filled():
		loop = asyncio.get_event_loop()
		loop.run_until_complete(main())
	else:
		print('Specify all variables in the config file!')
