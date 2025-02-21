import csv
import os
import threading
from argparse import ArgumentParser
import time
import yaml
import pandas as pd
from web3 import Web3
from requests.exceptions import HTTPError

with open('config.yaml') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

num_value_errors = 0
nThreads = 8
step_size = 100 # 200 result in a value error for some requests

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

# work is distributed to threads
def get_past_logs_threaded(w3, address, topic, file_path, num_threads, start_block, end_block):

    tmp_files = [file_path.split(".")[0] + "_" + str(i) + ".csv" for i in range(num_threads)]
    threads = []

    block_range = end_block - start_block
    thread_block_rate = block_range/num_threads

    for i in range(num_threads):
        _start_block = int(start_block + i * thread_block_rate)
        _end_block = int(start_block + (i+1) * thread_block_rate - 1)

        if (i == num_threads - 1):
            end_block = end_block + 1   # add one more for the last thread range:

        print(f"thread {i}: start block: {_start_block}, end block: {_end_block})")
        threads.append(threading.Thread(target=get_past_logs_thread, args=(w3, address, topic, tmp_files[i], _start_block, _end_block, i)))

    # start threads
    for i in range(num_threads):
        threads[i].start()

    # wait for threads to finish
    for i in range(num_threads):
        threads[i].join()

    print(f"number of value errors: {num_value_errors}")
    if num_value_errors > 0:
        print("\n!!\n!!\n!! WARNING: there have been ValueErrors: output is incorrect! \n!!\n!!")

    # merge tmp csv files
    merge_csv_files(tmp_files, file_path)

def merge_csv_files(files, final_file):

    # somehow replacing the file does not work with open mode "w" ??
    # therefore i remove it, when it exists
    if os.path.exists(final_file):
        os.remove(final_file)

    with open(final_file, mode='w') as f1:
        writer = csv.writer(f1)
        f1.write("tx_hash,block_number,from,to,amount\n")

        # write tmp files to final_file
        for file in files:
            with open(file, mode='r') as f2:
                reader = csv.reader(f2)
                for row in reader:
                    writer.writerow(row)

        # remove tmp files
        for file in files:
            if os.path.exists(file):
                os.remove(file)

def perform_get_logs_with_too_many_requests_protection(w3, filter, thread_num):
    sleeping_time = 1
    done = False
    while not done:
        try:
            result = w3.eth.get_logs(filter)
        except HTTPError as e:
            if e.response.status_code == 429:
                print(f"[thread {thread_num}] Too many request error. Retrying in {sleeping_time} seconds...")
                time.sleep(sleeping_time)
                sleeping_time *= 2

            continue
        done = True
    return result

# each thread calls this function
def get_past_logs_thread(w3, address, topic, file_path, start_block, end_block, thread_num):
    global num_value_errors
    num_of_blocks = 0

    from_block = start_block
    to_block = from_block + step_size

    while True:
        try:
            start = time.time_ns()
            if from_block >= end_block:
                break
            if to_block > end_block:
                to_block = end_block

            filter = {
                'fromBlock': from_block,
                'toBlock': to_block,
                'address': address,
                'topics': [topic]
            }

            print(f"[thread {thread_num}] from block: {from_block}; to block: {to_block};")
            print(f"[thread {thread_num}] number of blocks: {to_block - from_block}")

            logs = perform_get_logs_with_too_many_requests_protection(w3, filter, thread_num)
            end_request = time.time_ns()
            num_of_blocks = num_of_blocks + (to_block - from_block)

            df = pd.DataFrame()

            print(f'[thread {thread_num}] len(logs): {len(logs)}')
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

            df.to_csv(file_path, index=False, header=False, mode='a')
            end_total = time.time_ns()

            print(f'[thread {thread_num}] Time for request: {(end_request - start) / 1_000_000} ms')
            print(f'[thread {thread_num}] Time total: {(end_total - start) / 1_000_000} ms')
            print(f'[thread {thread_num}] Total number of bloks: {num_of_blocks}')

            from_block = to_block + 1
            to_block = from_block + step_size

        except ValueError as ve:
            print('ValueError: ', ve)
            num_value_errors = num_value_errors + 1
            break
        except RuntimeError as e:
            print('Error getting logs: ', e)
            break

def get_block_number_of_first_log(w3, address, topic, end_block):

    from_block = int(0)
    to_block = int(end_block)

    try:
        filter = {
            'fromBlock': from_block,
            'toBlock': to_block,
            'address': address,
            'topics': [topic]
        }

        print(f"from block: {from_block}; to block: {to_block};")
        print(f"number of blocks: {to_block - from_block}")

        w3.eth.get_logs(filter)

    # ValueError is used to get earliest from_block value
    except ValueError as ve:
        print('ValueError: ', ve)
        # print(ve.args.get)
        suggested_start_block = str(ve.args).split("'from': '")[1].split("'")[0]
        print("Suggested start block: ", int(suggested_start_block, 16))
    except RuntimeError as e:
        print('Error getting logs: ', e)


def get_uint(data):
    return int.from_bytes(bytes.fromhex(data), byteorder="big", signed=False)


def get_int(data):
    return int.from_bytes(bytes.fromhex(data), byteorder="big", signed=True)


def split_data(data):
    return [data[i:i + 64] for i in range(2, len(data), 64)]

def main(args):
    end_block = int(args.end_block)

    start_time = time.time()
    if args.topic is None:
        print('Error: topic not specified')
    if args.address is None:
        print('Error: address not specified')

    if end_block is None:
        print('Error: end block must be specified')

    if args.output is None:
        print('Error: no output file specified')

    # connect to the Ethereum node
    if config["keys"]["infura_apikey"] is not None:
        eth_con = conETH(config["keys"]["infura_apikey"])

        # get start block if none_specified
        if args.start_block is None:
            print('Expect ValueError...')
            get_block_number_of_first_log(eth_con, args.address, args.topic, args.end_block)
            print('Error: start block must be specified')
            return

        start_block = int(args.start_block)

        # make the query
        if eth_con is not None:
            get_past_logs_threaded(eth_con, args.address, args.topic, args.output, nThreads, start_block, end_block)
        else:
            print("Error: connection to the ethereum node failed")
            return
    else:
        print("Error: infura api key not found")
        return

    end_time = time.time()
    print(f"Total time: {end_time - start_time} s")


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-a', '--address',
                        help='Filter for the contract address', type=str, required=True)
    parser.add_argument('--start-block',
                        help='Start block for the filter operation', type=str, required=False)
    parser.add_argument('--end-block',
                        help='End block for the filter operation', type=str, required=True)
    parser.add_argument('-t', '--topic',
                        help='Filter for the given topic', type=str, required=True)
    parser.add_argument('-o', '--output',
                        help='Output file path (JSON)', type=str, required=True)
    args = parser.parse_args()

    main(args)
