#!/usr/bin/python
from decimal import Decimal
import pandas as pd
from argparse import ArgumentParser
from bs4 import BeautifulSoup


def create_balance_df(file, end_block=19955500):
    df = pd.read_csv(file)
    df["amount"] = df["amount"].apply(Decimal)

    df = df[df["block_number"] <= end_block]
    print("unique columns: ", df.nunique())

    df_total = compute_address_balances(df, end_block)
    return df_total


def compute_address_balances(df, at=None):
    block_range = df.iloc[-1]["block_number"] - df.iloc[0]["block_number"]
    if at is not None:
        df = df[df["block_number"] <= at]
    to_group = df.groupby(['to']).agg(
        amount=('amount', 'sum'),
        transfer_frequency=('amount', 'count')      # transfer count
    )
    to_group['transfer_frequency'] = to_group['transfer_frequency'] / block_range
    to_group.index.names = ['address']
    # print("to unique: ", to_group.nunique())
    from_group = df.groupby(['from']).agg(
        amount=('amount', 'sum'),
        transfer_frequency=('amount', 'count')      # transfer count
    )
    from_group['transfer_frequency'] = from_group['transfer_frequency'] / block_range
    from_group.index.names = ['address']
    # print("from unique: ", from_group.nunique())

    df_total = pd.merge(to_group, from_group, left_index=True, right_index=True, suffixes=("_in", "_out"),
                        how="outer").fillna(0)
    df_total["balance"] = df_total["amount_in"] - df_total["amount_out"]
    df_total = df_total.reset_index()
    df_total['address'] = df_total['address'].apply(lambda addr: "0x" + addr[-40:])

    return df_total


def parse_html(html_file):
    HTMLFile = open(html_file, "r")
    index = HTMLFile.read()
    soup = BeautifulSoup(index, 'lxml')
    exchanges = {}
    curr_ex = ''
    for t in soup.tbody.children:
        if t.attrs == {}:
            continue
        if t['class'][0] == 'address-row':
            curr_ex = t['data-code']
            exchanges[curr_ex] = []
            print('parsing exchange ' + curr_ex)
        elif t['class'][0] == 'chain-expand':
            exchanges[curr_ex].append(t['id'])

    return exchanges


def parse_and_assign_cex(html_file, df):
    cex_addresses = parse_html(html_file)

    def assign_cex(address):
        for name, addresses in cex_addresses.items():
            if address in addresses:
                return name

    df['cex'] = df["address"].apply(assign_cex)
    return df


# remove negative values
def clean_data(df):
    non_negative_balances = df.loc[df["balance"] >= 0]
    return non_negative_balances.sort_values(by=["balance"], ascending=False)


def remove_zero_balances(df):
    non_zero_balances = df.loc[df["balance"] != 0]
    return non_zero_balances


def remove_address(df: pd.DataFrame, address):
    if address is not None:
        result = df.loc[df["address"] != address] #df.drop(index=address)
        return result
    return None


def main(args):
    if args.file is None:
        print('Error: Please specify the file to analyze')

    df_total = create_balance_df(args.file)
    df_total = parse_and_assign_cex("data/Ethereum(ETH) Exchange Wallet Address List and Balance Change _ CoinCarp.html", df_total)
    df_total.to_csv(args.out)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file',
                        help='Path for file', type=str, required=True)
    parser.add_argument('--out', '-o',
                        help='Path for output file', type=str, required=True)

    args = parser.parse_args()

    main(args)
