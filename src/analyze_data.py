import random
from argparse import ArgumentParser
from decimal import Decimal

from matplotlib import pyplot as plt
from matplotlib import colors as mcolors
import pandas as pd
import numpy as np
from preprocess_data import create_balance_df, compute_address_balances

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

# https://lifewithdata.com/2023/05/24/how-to-calculate-the-gini-coefficient-in-python/
def gini(x):
    # The rest of the values must be sorted:
    x = np.sort(x)
    # Index per data point
    index = np.arange(1, x.shape[0] + 1)
    # Number of data points
    n = x.shape[0]
    # Gini coefficient calculation

    # alternative (same as in wikipedia)
    # gini = float((2 * np.sum(index * x)) / (n * np.sum(x))) - ((n+1)/n)
    return ((np.sum((2 * index - n  - 1) * x)) / (n * np.sum(x)))

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

def merge_others_at_cut_off_value(df, cut_point):
    df_prepared = df.head(cut_point)
    df_rest = df.iloc[cut_point:]
    sum_others = df_rest["balance"].sum()
    # print("sum: ", sum_others)
    row = pd.DataFrame({"address": "others", "balance": sum_others}, index=[0])
    return pd.concat([df_prepared, row], ignore_index=True)


def create_and_export_gini_timeline(file_original, step_size, file_output=None):
    df = pd.read_csv(file_original)
    df["amount"] = df["amount"].apply(Decimal)

    start_block = df.iloc[0]["block_number"]
    end_block = df.iloc[-1]["block_number"]
    gini_indices = []
    for block in range(start_block+step_size, end_block, step_size):
        print(f"[Gini][Timeline][Block {block}]: Calculating balances ...")
        df_balances = compute_address_balances(df, block)

        df_balances = df_balances.reset_index()

        # clean
        non_negative_df = clean_data(df_balances)
        only_positive_df = remove_zero_balances(non_negative_df)
        only_positive_df_removed_timelockAddress = remove_address(only_positive_df, "0x0000000000000000000000001a9c8182c09f50c8318d769245bea52c32be35bc")

        print(f"[Gini][Timeline][Block {block}]: Calculating gini ...")
        gini_index = compute_gini_index(only_positive_df_removed_timelockAddress)
        gini_indices.append({
            "gini_index": gini_index,
            "block_number": block
        })
        print(f"[Gini][Timeline][Block {block}]: Done calculating: {gini_index}")

    print(f"[Gini][Timeline]: Done")
    gini_df = pd.DataFrame.from_records(gini_indices, index="block_number")
    if file_output is not None:
        gini_df.to_csv(file_output)
    return gini_df

def create_timeline_plot(data):
    data.plot()

# def main(args):
#     if args.file_balances is None or args.file_original is None:
#         print('Error: Please specify the two files required for analysis')
#
#     df = pd.read_csv(args.file_balances)
#     df["balance"] = df["balance"].apply(Decimal)
#     df["amount_in"] = df["amount_in"].apply(Decimal)
#     df["amount_out"] = df["amount_out"].apply(Decimal)
#
#     cleaned_df = clean_data(df)
#     processed_df = merge_others_at_cut_off_value(cleaned_df, 50)
#     processed_df_cutPoint100 = merge_others_at_cut_off_value(cleaned_df, 100)
#
#     # --------- compute metrics
#
#     # ----- How are governance tokens distributed?
#
#     # gini coefficient
#     #gini_index = compute_gini_index(cleaned_df)
#     #print("gini index: ", gini_index)
#
#     # TODO: maybe: herfindahl hirschman index
#     hh_index = compute_herfindahl_hirschman_index(cleaned_df)
#     print("hh index: ", hh_index)
#
#     # Percentage of tokens held by
#     # - top 10
#     # - top 100
#     # - top 1000
#     # print_top_percentages(cleaned_df)
#
#     # ----- Who and how often trades them?
#
#     # min, max and avg of total number of sent tokens
#     # top 10 token senders
#     # top 10 token receivers
#     # print_top_traders(cleaned_df)
#
#     # tokens sent per block
#     print_tokens_per_block(args.file_original)
#
#     # min, max and avg transaction frequencies
#
#     # ----- What fraction is held by CEXs, and what by users?
#
#     # graphs
#     create_pie_chart(processed_df, "../data/uniswap_pie_chart.png")
#     create_pie_chart(processed_df_cutPoint100, "../data/uniswap_pie_chart_cutPoint100.png")
#
#     # create_pie_chart(processed_df.drop(index=0), "../data/uniswap_pie_chart_withoutTopHolder.png") # without top balance holder
#
#     create_bar_chart(processed_df, "../data/uniswap_bar_chart.png")
#
#     # analysis of CEX addresses
#
#     # ----- Timeline analysis
#     # gini index every n_timeline blocks
#     # gini_indices = create_gini_timeline(args.file_original, 10861674, 19955500, 100_000)
#     # print("gini indices: ", gini_indices)
#
#
# if __name__ == '__main__':
#     parser = ArgumentParser()
#     parser.add_argument('--file-original',
#                         help='Path for original file of all transfers logs', type=str, required=True)
#     parser.add_argument('--file-balances',
#                         help='Path for file that contains the balances', type=str, required=True)
#     # parser.add_argument('--out', '-o',
#     #                     help='Path for output file', type=str, required=True)
#
#     args = parser.parse_args()
#     main(args)
