#!/usr/bin/python
from argparse import ArgumentParser
import pandas as pd

def analyze_data(file, out):
    pd.options.display.max_colwidth = 68
    pd.set_option('float_format', '{:f}'.format)

    df = pd.read_csv(file)
    df["amount"] = df["amount"].astype(float)

    print("unique columns: ", df.nunique())

    to_group = df.groupby(['to']).agg({'amount': 'sum'})
    to_group.index.names = ['address']
    # print("to unique: ", to_group.nunique())
    from_group = df.groupby(['from']).agg({'amount': 'sum'})
    from_group.index.names = ['address']
    # print("from unique: ", from_group.nunique())

    df_total = pd.merge(to_group, from_group, left_index=True, right_index=True, suffixes=("_in", "_out"), how="outer").fillna(0)
    df_total["balance"] = df_total["amount_in"] - df_total["amount_out"]
    # df_total

    df_total_negativeBalance = df_total.loc[df_total["balance"] < 0]

    # df['total_tokens'] =
    # print(to_group)
    # print(from_group)
    print(df_total)
    # df_total.to_csv(out)
    print(df_total_negativeBalance)




def main(args):
    if args.file is None:
        print('Error: Please specify the file to analyze')

    analyze_data(args.file, args.out)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file',
                        help='Path for file', type=str, required=True)
    parser.add_argument('--out', '-o',
                        help='Path for output file', type=str, required=True)

    args = parser.parse_args()

    main(args)