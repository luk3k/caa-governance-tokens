from argparse import ArgumentParser
import json

import web3.exceptions
import yaml
import pandas as pd
from web3 import Web3
from web3._utils.events import get_event_data

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)


# connection to the ethereum node
def conETH(infura_api):
    # url link to the ethereum node
    url_eth_mainnet = "https://mainnet.infura.io/v3/"
    try:
        # connect to the ethereum node
        con = Web3(Web3.HTTPProvider(url_eth_mainnet + infura_api))
        return con
    except:
        return None


# get transaction by hash
def get_past_logs(w3, topic):
    try:
        result = pd.DataFrame()
        filter = {
            'fromBlock': 19955165,
            'toBlock': 19955175,
            'address': '0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984',
            'topics': ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]
        }
        logs = w3.eth.get_logs(filter)
        print(f'logs: {len(logs)}\n + {str(logs)}')
        for l in logs:
            filtered_log = {
                'from': bytes.hex(l['topics'][1]),
                'to': bytes.hex(l['topics'][2]),
                'amount': get_uint(bytes.hex(l['data']))
            }
            new_df = pd.DataFrame.from_dict(filtered_log)
            result = pd.concat([result, new_df])
            print("0x" + bytes.hex(l["transactionHash"]))

        return result
    except RuntimeError as e:
        print('Error getting logs: ', e)
        return None


def get_uint(data):
    return int.from_bytes(bytes.fromhex(data), byteorder="big", signed=False)


def get_int(data):
    return int.from_bytes(bytes.fromhex(data), byteorder="big", signed=True)

def split_data(data):
    return [data[i:i + 64] for i in range(2, len(data), 64)]

def get_transfers(w3, tx_hash):
    try:
        logs = w3.eth.get_transaction_receipt(tx_hash).logs

        # ---- implement this part ----

        # logs_filtered = # .... filter logs for the Uniswap V3 swap event from wETH-USDC pool
        # swap_event = logs_filtered[0] # ... get the first swap event

        # return {
        #     "amount0": int(0),  # ... amount of token0 sent to the contract
        #     "amount1": int(0),  # ... amount of token1 sent to the contract
        #     "sqrtPriceX96": int(0),  # ... price representation
        # }

        # ----------------------------

        uniswap_topic = '0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67'
        logs_filtered = list(filter(lambda log: uniswap_topic in list(map(lambda t: t.hex(), log['topics'])), logs))
        transfer_event = logs_filtered[0]
        event_abi = """
        [{
            "anonymous": false,
            "inputs": [
                {
                    "type": "address",
                    "name": "from",
                    "indexed": true
                },
                {
                    "type": "address",
                    "name": "to",
                    "indexed": true
                },
                {
                    "type": "uint256",
                    "name": "amount",
                    "indexed": false
                }
            ],
            "name": "Transfer",
            "type": "event"
        }]"""
        transfer_event_abi = w3.eth.contract(abi=event_abi)
        evt = get_event_data(w3.codec, transfer_event_abi.events.Swap._get_event_abi(), transfer_event)
        return {
            'amount0': evt['args']['amount0'],
            'amount1': evt['args']['amount1'],
            'sqrtPriceX96': evt['args']['sqrtPriceX96'],
        }
    except web3.exceptions.TransactionNotFound:
        return None


def main(args):
    if args.topic is None:
        print('Error: topic not specified')
    # connect to the Ethereum node
    if config["keys"]["infura_api"] is not None:
        eth_con = conETH(config["keys"]["infura_api"])
        # make the query
        if eth_con is not None:
            result = get_past_logs(eth_con, args.topic)
        else:
            print("Error: connection to the ethereum node failed")
            return
    else:
        print("Error: infura api key not found")
        return

    # save the result into a JSON file
    if args.output is not None:
        # with open(args.output, 'w') as f:
        #     json.dump(result, f)
        print(result)
    else:
        print("Error: no output defined")
        return


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-t', '--topic',
                        help='Filter for the given topic', type=str, required=True)
    parser.add_argument('-o', '--output',
                        help='Output file path (JSON)', type=str, required=True)
    args = parser.parse_args()

    main(args)
