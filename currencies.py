import asyncio
import csv
import os

from config import okx_credentials, logger
from py_okx_async.OKXClient import OKXClient


def get_unique_filename(directory: str, base_filename: str) -> str:
    if not os.path.exists(directory):
        os.makedirs(directory)
    base_path = os.path.join(directory, base_filename)
    filename, extension = os.path.splitext(base_path)
    counter = 1
    new_filename = f"{filename}{extension}"
    while os.path.exists(new_filename):
        new_filename = f"{filename}_{counter}{extension}"
        counter += 1
    return new_filename

async def curr(list: bool = False, dict: bool =False):
	'''
	get the names and networks of supporting tokens/coins
	:returns json file named supporting_tokens.csv
	'''
	okx_client = OKXClient(credentials=okx_credentials)
	data =await okx_client.asset.currencies()
	csv_data = []

	if list:
		for token, networks in data.items():
			csv_data.append(token)
		return csv_data

	if dict:
		dict={}
		for token, networks in data.items():
			for network, details in networks.items():
				chain=details.chain
			dict[chain.upper()] = chain
		return dict


	for token, networks in data.items():
		for network, details in networks.items():
			csv_data.append({
				'Token': token,
				'Network': details.chain
			})

	results_dir='supporting_tokens'
	output_file = get_unique_filename(results_dir, 'supporting_tokens.csv')

	with open(output_file, mode='w', newline='', encoding='utf-8') as csv_file:
		writer = csv.DictWriter(csv_file, fieldnames=['Token', 'Network'])
		writer.writeheader()
		writer.writerows(csv_data)

	logger.info(f'Данные успешно сохранены в файл {output_file}')


if __name__ == '__main__':
	if okx_credentials.completely_filled():
		loop = asyncio.get_event_loop()
		loop.run_until_complete(curr())
	else:
		print('Specify all variables in the config file!')

