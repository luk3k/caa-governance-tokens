import random
from argparse import ArgumentParser
from decimal import Decimal

from matplotlib import pyplot as plt
from matplotlib import colors as mcolors
import pandas as pd
import numpy as np
from preprocess_data import create_balance_df

pd.options.display.max_colwidth = 68


def create_pie_chart(df, output_path):
    plt.figure()
    data = df["balance"].to_numpy()
    addresses = df["address"].apply(lambda x: x.replace("000000000000000000000000", "")).apply(lambda x: x[0:7])
    colors = random.choices(list(mcolors.CSS4_COLORS.values()), k=len(addresses))
    wedges, texts = plt.pie(data,
            labels=addresses,
            colors=colors)
    # plt.legend(wedges, addresses,
    #            loc="center left",
    #            bbox_to_anchor=(1.04, 0.5),
    #            borderaxespad=0)

    plt.savefig(output_path)


def create_bar_chart(df, output_path):
    plt.figure()
    addresses = df["address"]
    data = df["balance"].to_numpy()
    plt.barh(addresses, data)
    plt.savefig(output_path)


def print_top_percentages(df):
    sum = df["balance"].sum()

    top_10_balance = (df.iloc[:10])["balance"].sum()
    top_10_percentage = top_10_balance/sum
    print(f"Top 10 percentage: {round(top_10_percentage * 100, 2)}%\n")

    top_100_balance = (df.iloc[:100])["balance"].sum()
    top_100_percentage = top_100_balance/sum
    print(f"Top 100 percentage: {round(top_100_percentage * 100, 2)}%\n")

    top_1000_balance = (df.iloc[:1000])["balance"].sum()
    top_1000_percentage = top_1000_balance/sum
    print(f"Top 1000 percentage: {round(top_1000_percentage * 100, 2)}%\n")


def print_top_traders(df):
    top_receivers = df.sort_values(by="amount_in", ascending=False).iloc[:10]
    top_senders = df.sort_values(by="amount_out", ascending=False).iloc[:10]
    print(f"Top senders: {top_senders}\n")
    print(f"Top receivers: {top_receivers}\n")


def print_tokens_per_block(file):
    with open(file, mode='r') as f1:
        lines = f1.readlines()
        row_count = len(lines) - 1
        start_block = int(lines[1].split(',')[1])
        end_block = int(lines[-1].split(',')[1])

    r = end_block - start_block
    tx_per_block = r/row_count

    print(f"Token transfers per block: {round(tx_per_block, 2)}\n")


# https://en.wikipedia.org/wiki/Herfindahl%E2%80%93Hirschman_index
def compute_herfindahl_hirschman_index(df):
    # TODO
    return "TODO"


def compute_gini_index(df):
    balances = df["balance"].to_numpy()
    return gini(balances)


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


def create_gini_timeline(file_original, start, end, step_size):
    # TODO: Maybe remove top address
    gini_indices = []
    for block in range(start+step_size, end, step_size):
        df = create_balance_df(file_original, block)
        gini_indices.append({
            "gini_index": compute_gini_index(df),
            "block_number": block
        })
    return gini_indices

def create_timeline_plot():
    pass
    # TODO

def main(args):
    if args.file_balances is None or args.file_original is None:
        print('Error: Please specify the two files required for analysis')

    df = pd.read_csv(args.file_balances)
    df["balance"] = df["balance"].apply(Decimal)
    df["amount_in"] = df["amount_in"].apply(Decimal)
    df["amount_out"] = df["amount_out"].apply(Decimal)

    cleaned_df = clean_data(df)
    processed_df = merge_others_at_cut_off_value(cleaned_df, 50)
    processed_df_cutPoint100 = merge_others_at_cut_off_value(cleaned_df, 100)

    # --------- compute metrics

    # ----- How are governance tokens distributed?

    # gini coefficient
    #gini_index = compute_gini_index(cleaned_df)
    #print("gini index: ", gini_index)

    # TODO: maybe: herfindahl hirschman index
    hh_index = compute_herfindahl_hirschman_index(cleaned_df)
    print("hh index: ", hh_index)

    # Percentage of tokens held by
    # - top 10
    # - top 100
    # - top 1000
    # print_top_percentages(cleaned_df)

    # ----- Who and how often trades them?

    # min, max and avg of total number of sent tokens
    # top 10 token senders
    # top 10 token receivers
    # print_top_traders(cleaned_df)

    # tokens sent per block
    print_tokens_per_block(args.file_original)

    # min, max and avg transaction frequencies

    # ----- What fraction is held by CEXs, and what by users?

    # graphs
    create_pie_chart(processed_df, "../data/uniswap_pie_chart.png")
    create_pie_chart(processed_df_cutPoint100, "../data/uniswap_pie_chart_cutPoint100.png")

    # create_pie_chart(processed_df.drop(index=0), "../data/uniswap_pie_chart_withoutTopHolder.png") # without top balance holder

    create_bar_chart(processed_df, "../data/uniswap_bar_chart.png")

    # analysis of CEX addresses

    # ----- Timeline analysis
    # gini index every n_timeline blocks
    # gini_indices = create_gini_timeline(args.file_original, 10861674, 19955500, 100_000)
    # print("gini indices: ", gini_indices)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--file-original',
                        help='Path for original file of all transfers logs', type=str, required=True)
    parser.add_argument('--file-balances',
                        help='Path for file that contains the balances', type=str, required=True)
    # parser.add_argument('--out', '-o',
    #                     help='Path for output file', type=str, required=True)

    args = parser.parse_args()
    main(args)
