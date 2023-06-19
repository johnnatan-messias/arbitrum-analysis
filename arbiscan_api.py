import itertools
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import requests
from tqdm.notebook import tqdm


class ArbiscanAPI:

    def __init__(self, api_url='https://api.arbiscan.io/api', arbiscan_api_key=None):
        self.__api_url = api_url
        self.arbiscan_api_key = arbiscan_api_key
        self.__headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-us',
            'Connection': 'keep-alive',
            'Host': 'api.arbiscan.io',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_3) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.5 Safari/605.1.15'
        }

    def __dec_to_hex(self, dec):
        return hex(dec)

    def __hex_to_dec(self, hex_str):
        return int(hex_str, 16)

    def get_abi(self, contract_address):
        # Get contract ABI from Arbiscan
        params = {'module': 'contract', 'action': 'getabi',
                  'address': contract_address, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_transaction(self, txhash):
        # Get transaction from Arbiscan
        params = {'module': 'transaction', 'action': 'getstatus',
                  'txhash': txhash, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_block(self, block_number):
        # Get block from Arbiscan
        params = {'module': 'block', 'action': 'getblockreward',
                  'blockno': block_number, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_block_countdown(self, block_number):
        # Get block countdown from Arbiscan
        params = {'module': 'block', 'action': 'getblockcountdown',
                  'blockno': block_number, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_transaction_by_hash(self, txhash):
        # Get transaction by hash from Arbiscan
        params = {'module': 'proxy', 'action': 'eth_getTransactionByHash',
                  'txhash': txhash, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_block_by_number(self, block_number, include_txs=True):
        # Get block by number from Arbiscan
        params = {'module': 'proxy', 'action': 'eth_getBlockByNumber',
                  'tag': self.__dec_to_hex(block_number), 'boolean': include_txs, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_transaction_receipt(self, txhash):
        # Get transaction receipt from Arbiscan
        params = {'module': 'proxy', 'action': 'eth_getTransactionReceipt',
                  'txhash': txhash, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_block_by_time(self, timestamp, closest):
        # Get block by time from Arbiscan
        params = {'module': 'block', 'action': 'getblocknobytime',
                  'timestamp': timestamp, 'closest': closest, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_logs(self, contract_address, from_block, to_block, page=1, offset=10000):
        # Get logs from Arbiscan
        params = {'module': 'logs', 'action': 'getLogs', 'address': contract_address,
                  'fromBlock': from_block, 'toBlock': to_block, 'page': page, 'offset': offset, 'apikey': self.arbiscan_api_key}
        return self.__get_response(params)

    def get_logs2(self, args):
        # Get logs from Arbiscan
        params = {'module': 'logs', 'action': 'getLogs', 'address': args['contract_address'],
                  'fromBlock': args['from_block'], 'toBlock': args['to_block'], 'page': 1, 'offset': 10000, 'apikey': self.arbiscan_api_key}
        # Introduced a delay to avoid reaching the Arbiscan API rate limit
        # Note: The rate limit is 5 requests per second
        time.sleep(0.3)
        return self.__get_response(params)

    def get_logs_in_batches(self, contract_address, from_block, to_block, batch_size=1000, max_workers=2):
        # Get logs from Arbiscan in batches
        logs_data = list()
        dict_keys = ['contract_address', 'from_block', 'to_block']
        intervals = self.get_batch_intervals(
            block_start=from_block, block_end=to_block, batch_size=batch_size)

        intervals = list(dict(zip(dict_keys, (contract_address, *interval)))
                         for interval in intervals)
        print(intervals)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            logs_data = list(
                tqdm(pool.map(self.get_logs2, intervals), total=len(intervals), desc="Gathering logs data"))
        # logs_data = list(itertools.chain(*logs_data))
        return logs_data

    def get_batch_intervals(self, block_start, block_end, batch_size):
        intervals = list()
        block_numbers = list(range(block_start, block_end, batch_size))
        for block_number in block_numbers:
            block_interval_start = block_number
            block_interval_end = min(block_number + batch_size - 1, block_end)
            intervals.append((block_interval_start, block_interval_end))
        return intervals

    def __get_response(self, params):
        ans = {}
        nerr = 5
        while nerr > 0:
            try:
                rq = requests.get(self.__api_url, headers=self.__headers,
                                  params=params, timeout=20)
                if rq.status_code == 200:
                    ans = rq.json()
                    rq.connection.close()
                    break
            except:
                print("Error on requesting data from Arbiscan",
                      traceback.print_exc())
                time.sleep(1)
            nerr -= 1
        return ans

    def getHeader(self):
        return self.__headers

    def setHeader(self, header):
        self.__headers = header
