# caa-governance-tokens
Analyse governance token flows for selected etheureum DeFi protocols

## Usage of scripts

### `read_data.py`:

Parameters:
- -a ... address
- -t ... topic
- -o ... output file
- --start-block
- --end-block

Option 1: Don't specify `--start-block` to discover the suggested start block:
```
python read_data.py -a 0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2 -t 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef -o data/outputMKR_fromBlock_X_toBlock_Y --end-block 19966660
```

Option 2: Specify `--start-block` and `--end-block` to fetch all log events:
```
python read_data.py -a 0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2 -t 0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef -o data/outputMKR_2_fromBlock_6620856_toBlock_8620856 --start-block 6620856 --end-block 8620856
```


## Tokens and data

End block: 19966660

Uniswap: 
- Transfer event signature: `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef`
- Token Holder chart: https://etherscan.io/token/tokenholderchart/0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984
- UNI token: https://etherscan.io/token/0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984
- Start block: 10876695

DAI (MKR Token):
- Transfer event signature: `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef`
- Token Holder chart: https://etherscan.io/token/tokenholderchart/0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2
- MKR Token: https://etherscan.io/address/0x9f8f72aa9304c8b593d555f12ef6589cc3a579a2**
- Start block: 4620855
- Fetch data:
  - Range of blocks: 15.345.805
  - First packet: 4620855 - 6620855 (3.000.000 blocks)
    - number of value errors: 0 
    - Total time: 1895.4309995174408 s
  - Second packet: 6620856 - 8620856


