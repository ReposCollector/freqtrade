from freqtrade.data.btanalysis import load_backtest_data
df = load_backtest_data("../backtest_data/backtest_syko_strategy.json")

# Show value-counts per pair
df.groupby("pair")["sell_reason"].value_counts()

print(df)