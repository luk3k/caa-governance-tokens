import random
from argparse import ArgumentParser
from decimal import Decimal
from matplotlib import pyplot as plt
from matplotlib import colors as mcolors
import pandas as pd
import numpy as np
from matplotlib.ticker import ScalarFormatter
from preprocess_data import compute_address_balances, clean_data, remove_zero_balances, remove_address

pd.options.display.max_colwidth = 68


def create_pie_chart(df, output_path, labels=None, show_legend=False):
    plt.figure(figsize=(12, 4))
    data = df["balance"].to_numpy()
    if labels is None:
        addresses = df["address"].apply(lambda x: x[0:7] + "...")
        labels = addresses

    # colors = random.choices(list(mcolors.CSS4_COLORS.values()), k=len(labels))
    colors = ["#575757", "#b2b08f", "#17726d", "#eae4d2", "#f6f6f6", "#ffc700"]
    wedges, texts = plt.pie(data,
                            labels=labels,
                            colors=colors)
    if show_legend:
        plt.legend(wedges, labels,
                   loc="center left",
                   bbox_to_anchor=(1.2, 0.5),
                   borderaxespad=0)
        plt.tight_layout()

    plt.savefig(output_path, transparent=True)


def create_bar_chart(df, output_path):
    plt.figure(figsize=(12, 4))
    addresses = df["address"]
    data = df["balance"].to_numpy()
    plt.barh(addresses, data, color="#17726d")
    plt.savefig(output_path, transparent=True)


def print_cex_percentages(df):
    sum = df["balance"].sum()

    df_cex_not_none = df[~pd.isnull(df["cex"])]
    df_cex_is_none = df[pd.isnull(df["cex"])]

    cex_sum = df_cex_not_none["balance"].sum()
    others_sum = df_cex_is_none["balance"].sum()

    print(f"\nAll cex together hold {cex_sum} out of {sum} ({round((cex_sum / sum) * 100, 2)} %) tokens")
    print(f"Other addresses hold {others_sum} out of {sum} ({round((others_sum / sum) * 100, 2)} %) tokens")


def aggregate_cex_balances(df):
    """
    Returns a dataframe containing only central exchanges with their total balances.
    :param df: the dataframe to operate on
    :return: a new df containing only central exchanges with their total balances.
    """
    df_cex = df[~pd.isnull(df["cex"])]
    group = df_cex.groupby(['cex']).agg({'balance': 'sum'})
    group.index.names = ['cex']
    return group.reset_index()


def print_top_percentages(df):
    df = df.sort_values(by=["balance"], ascending=False)
    sum = df["balance"].sum()

    top_10_balance = (df.iloc[:10])["balance"].sum()
    top_10_percentage = top_10_balance / sum
    print(f"Top 10 percentage: {round(top_10_percentage * 100, 2)}%")

    top_100_balance = (df.iloc[:100])["balance"].sum()
    top_100_percentage = top_100_balance / sum
    print(f"Top 100 percentage: {round(top_100_percentage * 100, 2)}%")

    top_1000_balance = (df.iloc[:1000])["balance"].sum()
    top_1000_percentage = top_1000_balance / sum
    print(f"Top 1000 percentage: {round(top_1000_percentage * 100, 2)}%")


def print_top_traders(df):
    group = df.groupby(['cex']).agg(
        {'balance': 'sum', 'amount_in': 'sum', 'amount_out': 'sum', 'transfer_frequency_out': 'sum',
         'transfer_frequency_in': 'sum'})
    group.index.names = ['cex']
    df_aggregated = group.reset_index()
    df_aggregated = df_aggregated[~pd.isnull(df_aggregated['cex'])]
    df_aggregated = df_aggregated.append(df[pd.isnull(df['cex'])])

    top_receivers = df_aggregated.sort_values(by="amount_in", ascending=False).iloc[:10]
    top_senders = df_aggregated.sort_values(by="amount_out", ascending=False).iloc[:10]

    top_receivers["balance"] = top_receivers["balance"].apply(int)
    top_receivers["amount_in"] = top_receivers["amount_in"].apply(int)

    top_senders["balance"] = top_senders["balance"].apply(int)
    top_senders["amount_out"] = top_senders["amount_out"].apply(int)

    print(f"\nTop senders: ")
    print(f"{top_senders[['address', 'amount_out', 'balance', 'cex', ]]}")
    print(f"\nTop receivers: ")
    print(f"{top_receivers[['address', 'amount_in', 'balance', 'cex']]}")

    top_senders_transfer_frequency = df_aggregated.sort_values(by="transfer_frequency_out", ascending=False).iloc[:10]
    top_receivers_transfer_frequency = df_aggregated.sort_values(by="transfer_frequency_in", ascending=False).iloc[:10]

    top_senders_transfer_frequency["balance"] = top_senders_transfer_frequency["balance"].apply(int)
    top_receivers_transfer_frequency["balance"] = top_receivers_transfer_frequency["balance"].apply(int)

    print(f"\nMost active senders: ")
    print(f"{top_senders_transfer_frequency[['address', 'transfer_frequency_out', 'balance', 'cex']]}")
    print(f"\nMost active receivers: ")
    print(f"{top_receivers_transfer_frequency[['address', 'transfer_frequency_in', 'balance', 'cex']]}\n")


def print_transfer_frequency(file):
    with open(file, mode='r') as f1:
        lines = f1.readlines()
        row_count = len(lines) - 1
        start_block = int(lines[1].split(',')[1])
        end_block = int(lines[-1].split(',')[1])

    r = end_block - start_block
    transfer_frequency = row_count / r

    print(f"\nTransfer frequency: {round(transfer_frequency, 2)}")


# https://en.wikipedia.org/wiki/Herfindahl%E2%80%93Hirschman_index
# measures the market concentration: lower degree means closer to perfect distribution, higher degree means monopol
def compute_herfindahl_hirschman_index(df, top_n_player=None):
    num_players = df.shape[0]
    if top_n_player is None:
        top_n_player = num_players
    # df must be sorted!
    balances = df["balance"].to_numpy()
    total = balances.sum()
    hhi_elements = [(value / total) ** 2 for value in balances[:top_n_player]]
    hhi = float(sum(hhi_elements))
    print("hhi: ", hhi)
    hhi_normalized = (hhi - (1 / num_players)) / (1 - (1 / num_players))
    print("hhi_normalized: ", hhi_normalized)
    return hhi_normalized


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
    return float(((np.sum((2 * index - n - 1) * x)) / (n * np.sum(x))))


def merge_others_at_cut_off_value(df, cut_point):
    df_prepared = df.head(cut_point)
    df_rest = df.iloc[cut_point:]
    sum_others = df_rest["balance"].sum()
    row = pd.DataFrame({"address": "others", "balance": sum_others}, index=[0])
    return pd.concat([df_prepared, row], ignore_index=True)


def create_and_export_timeline(file_original, step_size, file_output=None, addresses_to_remove=[]):
    df = pd.read_csv(file_original)
    df["amount"] = df["amount"].apply(Decimal)

    start_block = df.iloc[0]["block_number"]
    end_block = df.iloc[-1]["block_number"]
    gini_indices = []
    txs_per_block = []
    hhis = []
    prev_block = start_block - 1
    for block in range(start_block + step_size, end_block, step_size):
        print(f"[Timeline][Block {block}]: Calculating balances ...")
        df_balances = compute_address_balances(df, block)

        df_balances = df_balances.reset_index()

        # clean
        non_negative_df = clean_data(df_balances)
        only_positive_df = remove_zero_balances(non_negative_df)
        only_positive_df_removed_addresses = only_positive_df
        for addr in addresses_to_remove:
            only_positive_df_removed_addresses = remove_address(only_positive_df, addr)

        print(f"Timeline][Block {block}]: Calculating gini ...")
        gini_index = compute_gini_index(only_positive_df_removed_addresses)
        gini_indices.append(gini_index)
        print(f"[Timeline][Block {block}]: Done calculating gini: {gini_index}")

        print(f"Timeline][Block {block}]: Calculating tx per block ...")
        tx_per_block = df[(df['block_number'] > prev_block) & (df['block_number'] <= block)].shape[0] / (
                    block - prev_block)
        txs_per_block.append(tx_per_block)
        print(f"Timeline][Block {block}]: Done Calculating tx per block: {tx_per_block}")

        print(f"Timeline][Block {block}]: Calculating hhi ...")
        hhi = compute_herfindahl_hirschman_index(only_positive_df_removed_addresses)
        hhis.append(hhi)
        print(f"[Timeline][Block {block}]: Done calculating hhi: {hhi}")
        prev_block = block

    print(f"[Timeline]: Done")
    # gini_df = pd.DataFrame.from_records(gini_indices, index="block_number")
    df = pd.DataFrame(
        {'block_number': list(range(start_block + step_size, end_block, step_size)),
         'gini_index': gini_indices,
         'tx_per_block': txs_per_block,
         'hhi': hhis
         })
    if file_output is not None:
        df.to_csv(file_output)
    return df


def create_timeline_plot(data, y, output_path):
    fig, axs = plt.subplots(figsize=(12, 4))
    # y_columns = ['gini_index', 'tx_per_block', 'hhi']
    # axs.set_yscale("log")
    if y == "gini_index":
        color = "#17726d"
    elif y == "tx_per_block":
        color = "#ffc700"
    else:
        color = "#575757"

    data.plot(x='block_number', y=y, kind='line', ax=axs, color=color)
    fig.savefig(output_path, transparent=True)


def get_top_by_balances(data, n):
    df = data.sort_values(by="balance", ascending=False)
    return df.head(n)


def create_distribution_plot(data, key, output_path):
    df = pd.DataFrame(data)
    df.sort_values(by=key, ascending=True, inplace=True)
    df[key] = df[key].astype(float)

    fig, axs = plt.subplots(figsize=(12, 4))

    df.plot.hist(column=key, bins=100, ax=axs, color="#17726d")

    axs.set_title(f"Distribution by {key}")
    axs.set_yscale("log")
    axs.set_xlabel("")
    # axs.tick_params(axis='x', labelrotation=80)
    fig.savefig(output_path, transparent=True)
    plt.show()


def create_balance_cdf_plot(data, output_path):
    df = pd.DataFrame(data)
    df.sort_values(by="balance", ascending=True, inplace=True)
    df["balance"] = df["balance"].astype(float)
    df["cumulative_sum"] = df["balance"].cumsum()

    fig, axs = plt.subplots(figsize=(12, 4))
    df.plot(x="address", y="cumulative_sum", kind="line", ax=axs, color="#17726d")

    axs.set_xlabel("Address")
    axs.set_ylabel("cdf")
    axs.set_xticks([])
    axs.set_yticks([])
    fig.savefig(output_path, transparent=True)
    plt.show()

