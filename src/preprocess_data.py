#!/usr/bin/python
from argparse import ArgumentParser
from decimal import Decimal

import pandas as pd


def create_balance_df(file, end_block=19955500):
    df = pd.read_csv(file)
    df["amount"] = df["amount"].apply(Decimal)

    df = df[df["block_number"] <= end_block]
    print("unique columns: ", df.nunique())

    df_total = compute_address_balances(df, end_block)
    return df_total


def compute_address_balances(df, at=None):
    if at is not None:
        df = df[df["block_number"] <= at]
    to_group = df.groupby(['to']).agg({'amount': 'sum'})
    to_group.index.names = ['address']
    # print("to unique: ", to_group.nunique())
    from_group = df.groupby(['from']).agg({'amount': 'sum'})
    from_group.index.names = ['address']
    # print("from unique: ", from_group.nunique())

    df_total = pd.merge(to_group, from_group, left_index=True, right_index=True, suffixes=("_in", "_out"),
                        how="outer").fillna(0)
    df_total["balance"] = df_total["amount_in"] - df_total["amount_out"]

    return df_total


def main(args):
    if args.file is None:
        print('Error: Please specify the file to analyze')

    df_total = create_balance_df(args.file)
    df_total.to_csv(args.out)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file',
                        help='Path for file', type=str, required=True)
    parser.add_argument('--out', '-o',
                        help='Path for output file', type=str, required=True)

    args = parser.parse_args()

    main(args)
