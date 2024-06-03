from argparse import ArgumentParser
from decimal import Decimal

from matplotlib import pyplot as plt
import pandas as pd
import numpy as np


def create_pie_chart(df):
    plt.figure()
    data = df["balance"].to_numpy()
    addresses = df["address"]
    plt.pie(data, labels=addresses)
    plt.savefig("data/uniswap_pie_chart.png")


def create_bar_chart(df):
    plt.figure()
    addresses = df["address"]
    data = df["balance"].to_numpy()
    plt.barh(addresses, data)
    plt.savefig("data/uniswap_bar_chart.png")

# https://en.wikipedia.org/wiki/Herfindahl%E2%80%93Hirschman_index
def compute_herfindahl_hirschman_index(df):
    # TODO
    pass

def compute_gini_index(df):
    balances = df["balance"].to_numpy()
    print("gini index: ", gini(balances))


# gini index info: lies between 0 (max equality) and 1 (max inequality)
# gini reference values: https://en.wikipedia.org/wiki/Gini_coefficient
# source: https://www.statology.org/gini-coefficient-python/
def gini(x):
    total = 0
    for i, xi in enumerate(x[:-1], 1):
        total += np.sum(np.abs(xi - x[i:]))
    return total / (len(x) ** 2 * np.mean(x))


# remove negative values
def clean_data(df):
    non_negative_balances = df.loc[df["balance"] >= 0]
    return non_negative_balances.sort_values(by=["balance"], ascending=False)


def merge_others_at_cut_off_value(df, cut_point):
    df_prepared = df.head(cut_point)
    df_rest = df.iloc[cut_point:]
    sum_others = df_rest["balance"].sum()
    # print("sum: ", sum_others)
    row = pd.DataFrame({"address": "others", "balance": sum_others}, index=[0])
    return pd.concat([df_prepared, row], ignore_index=True)


def main(args):
    if args.file is None:
        print('Error: Please specify the file to analyze')

    df = pd.read_csv(args.file)
    df["balance"] = df["balance"].apply(Decimal)
    df["amount_in"] = df["amount_in"].apply(Decimal)
    df["amount_out"] = df["amount_out"].apply(Decimal)

    cleaned_df = clean_data(df)
    processed_df = merge_others_at_cut_off_value(cleaned_df, 20)
    create_pie_chart(processed_df)
    create_bar_chart(processed_df)
    compute_gini_index(cleaned_df)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file',
                        help='Path for file', type=str, required=True)
    # parser.add_argument('--out', '-o',
    #                     help='Path for output file', type=str, required=True)

    args = parser.parse_args()
    main(args)
