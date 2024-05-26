from argparse import ArgumentParser
import json
import time

import web3.exceptions
import yaml
import pandas as pd
from web3 import Web3
from web3._utils.events import get_event_data

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

analysis_end_block = 19955500
block_run_limit = 50_000


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
def get_past_logs(w3, address, topic, start_block, file_path):
    done = False
    # result = pd.DataFrame()
    step_size = 100
    num_of_blocks = 0

    from_block = "earliest" if start_block is None else int(start_block)
    to_block = analysis_end_block
    while num_of_blocks < block_run_limit:
        try:
            start = time.time_ns()
            if type(from_block) is not str and from_block >= analysis_end_block:
                break
            if to_block > analysis_end_block:
                to_block = analysis_end_block

            filter = {
                'fromBlock': from_block,
                'toBlock': to_block,
                'address': address,
                'topics': [topic]
            }

            print(f"from block: {from_block}; to block: {to_block};")
            if type(from_block) is not str and type(to_block) is not str:
                print(f"number of blocks: {to_block - from_block}")
            logs = w3.eth.get_logs(filter)

            end_request = time.time_ns()

            if type(from_block) is not str and type(to_block) is not str:
                num_of_blocks = num_of_blocks + (to_block - from_block)

            df = pd.DataFrame()

            print(f'logs: {len(logs)}')
            for l in logs:
                filtered_log = {
                    'tx_hash': [l['transactionHash'].hex()],
                    'block_number': [l['blockNumber']],
                    'from': [l['topics'][1].hex()],
                    'to': [l['topics'][2].hex()],
                    'amount': [get_uint(l['data'].hex()[2:])]
                }
                new_df = pd.DataFrame.from_dict(filtered_log)
                df = pd.concat([df, new_df])

                # result = pd.concat([result, new_df])
                # print("0x" + bytes.hex(l["transactionHash"]))

            df.to_csv(file_path, index=False, header=False, mode='a')
            end_total = time.time_ns()

            print(f'Time for request: {(end_request - start) / 1_000_000} ms')
            print(f'Time total: {(end_total - start) / 1_000_000} ms')
            print(f'Total number of bloks: {num_of_blocks}')
            print('\n')

            from_block = to_block + 1
            # to_block = analysis_end_block
            to_block = from_block + step_size

        # ValueError is used to get earliest from_block value
        except ValueError as ve:
            print('ValueError: ', ve)
            from_block = int(ve.args[0]["data"]["from"], 16)
            # to_block = int(ve.args[0]["data"]["to"], 16)
            to_block = from_block + step_size
        except RuntimeError as e:
            print('Error getting logs: ', e)

    print(f"Last block: {from_block - 1}")
    # return result


def get_uint(data):
    return int.from_bytes(bytes.fromhex(data), byteorder="big", signed=False)


def get_int(data):
    return int.from_bytes(bytes.fromhex(data), byteorder="big", signed=True)


def split_data(data):
    return [data[i:i + 64] for i in range(2, len(data), 64)]


def main(args):
    start_time = time.time()
    if args.topic is None:
        print('Error: topic not specified')
    if args.address is None:
        print('Error: address not specified')

    # init csv headers
    if args.start_block is None:
        with open(args.output, 'w') as f:
            f.write("tx_hash,block_number,from,to,amount\n")

    # connect to the Ethereum node
    if config["keys"]["infura_apikey"] is not None:
        eth_con = conETH(config["keys"]["infura_apikey"])
        # make the query
        if eth_con is not None:
            get_past_logs(eth_con, args.address, args.topic, start_block=args.start_block, file_path=args.output)
        else:
            print("Error: connection to the ethereum node failed")
            return
    else:
        print("Error: infura api key not found")
        return

    end_time = time.time()
    print(f"Total time: {end_time - start_time} s")
    # save the result into a JSON file
    # if args.output is not None and result is not None:
    #     result.to_csv(args.output, index=False)
    #     # print(result)
    # else:
    #     print("Error: no output defined")
    #     return


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-a', '--address',
                        help='Filter for the contract address', type=str, required=True)
    parser.add_argument('--start-block',
                        help='Start block for the filter operation', type=str, required=False)
    parser.add_argument('-t', '--topic',
                        help='Filter for the given topic', type=str, required=True)
    parser.add_argument('-o', '--output',
                        help='Output file path (JSON)', type=str, required=True)
    args = parser.parse_args()

    main(args)
