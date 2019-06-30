
# --- Do not remove these libs ---
from freqtrade.strategy.interface import IStrategy
from pandas import DataFrame
from freqtrade.order_item import OrderItem
# --------------------------------

# Add your lib to import here
import talib as talib
import talib.abstract as ta
from talib.test_data import series, assert_np_arrays_equal, assert_np_arrays_not_equal
import numpy as np
from nose.tools import assert_equals, assert_true, assert_raises
import freqtrade.vendor.qtpylib.indicators as qtpylib
import numpy  # noqa
import math
import matplotlib.pyplot as plt


# This class is a sample. Feel free to customize it.
class SykoStrategy(IStrategy):
    __test__ = False  # pytest expects to find tests here because of the name
    """
    This is a test strategy to inspire you.
    More information in https://github.com/freqtrade/freqtrade/blob/develop/docs/bot-optimization.md

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the prototype for the methods: minimal_roi, stoploss, populate_indicators, populate_buy_trend,
    populate_sell_trend, hyperopt_space, buy_strategy_generator
    """

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi"
    # The below configuration means:
    # - Sell whenever 4% profit was reached
    # - Sell when 2% profit was reached (in effect after 20 minutes)
    # - Sell when 1% profit was reached (in effect after 30 minutes)
    # - Sell when trade is non-loosing (in effect after 40 minutes)

    # minimal_roi = {
    #     "40": 0.0,
    #     "30": 0.01,
    #     "20": 0.02,
    #     "0": 0.04
    # }

    minimal_roi = {
        "1455": -1.00,
        "0": 0.3
    }

    # Optimal stoploss designed for the strategy
    # This attribute will be overridden if the config file contains "stoploss"
    stoploss = -0.04 # -2%

    # trailing stoploss
    trailing_stop = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Optimal ticker interval for the strategy
    ticker_interval = '1h'
    #tick_in_seconds = 60 * 5

    # run "populate_indicators" only for new candle
    process_only_new_candles = True

    # Experimental settings (configuration will overide these if set)
    use_sell_signal = False
    sell_profit_only = False
    ignore_roi_if_buy_signal = False

    # Optional order type mapping
    order_types = {
        'buy': 'limit',
        'sell': 'limit',
        'stoploss': 'market',
        'stoploss_on_exchange': False
    }

    # Optional order time in force
    order_time_in_force = {
        'buy': 'gtc',
        'sell': 'gtc'
    }


    def initialize_portfolio(self, config, pairs):
        self.config = config
        self.portfolio = dict()
        self.free_budget = dict()

        # 0: base_currency, 1: target_currency
        for pair in pairs:
            self.portfolio[pair] = dict()
            self.portfolio[pair][0] = int(self.config.get('stake_amount'))
            self.portfolio[pair][1] = 0
            self.free_budget[pair] = dict()
            self.free_budget[pair][0] = self.portfolio[pair][0]
            self.free_budget[pair][1] = 0


    def hours_to_ticks(self, hours):
        tick_in_seconds = 60 * 60
        return int(hours * 3600 / tick_in_seconds)

    def days_to_ticks(self, days):
        tick_in_seconds = 60 * 60
        return int(days * 24 * 3600 / tick_in_seconds)

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("ETH/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds several different TA indicators to the given DataFrame

        Performance Note: For the best performance be frugal on the number of indicators
        you are using. Let uncomment only the indicator you are using in your strategies
        or your hyperopt configuration, otherwise you will waste your memory and CPU usage.
        :param dataframe: Raw data from the exchange and parsed by parse_ticker_dataframe()
        :param metadata: Additional information, like the currently traded pair
        :return: a Dataframe with all mandatory indicators for the strategies
        """

        # Indicators
        # Range: (High - Low) during the last 24 hours
        # Larry_k: Average Noise Ratio during the last 20 days
        # Buy_Target: Target = Today Open + Range * Laary_k

        dataframe['donchian_up'] = talib.MAX(dataframe.high.shift(self.days_to_ticks(1)), timeperiod = self.days_to_ticks(1))
        dataframe['donchian_low'] = talib.MIN(dataframe.low.shift(self.days_to_ticks(1)), timeperiod = self.days_to_ticks(1))
        dataframe['donchian_range'] = abs(dataframe['donchian_up'] - dataframe['donchian_low'])

        dataframe['candle_noise'] = 1 - abs(dataframe.open - dataframe.close) / (abs(dataframe.high - dataframe.low) + 0.0000001)
        dataframe['larry_k'] = talib.MA(dataframe['candle_noise'], timeperiod = self.days_to_ticks(20))

        #dataframe['buy_target'] = dataframe.close.shift(self.days_to_ticks(1)) + 0.5 * dataframe['donchian_range']
        dataframe['buy_target'] = dataframe.close.shift(self.days_to_ticks(1)) + dataframe['larry_k'] * dataframe['donchian_range']
        #dataframe['buy_target'] = dataframe.open.shift(self.days_to_ticks(1)-1) + dataframe['larry_k'] * dataframe['donchian_range']

        #dataframe['buy_target'].plot()
        #plt.show()

        #dataframe['open'].plot()
        #plt.show()

        #filtered_df = dataframe[['date', 'close', 'open', 'high', 'low', 'donchian_range', 'larry_k', 'buy_target']]
        #buys = dataframe[dataframe.buy_target <= dataframe.open][['date', 'close', 'donchian_range', 'open', 'buy_target', 'high', 'low']]
        #print(buys)
        #print(filtered_df)
        #filtered_df

        # Moving Average
        # EMA - Exponential Moving Average
        #dataframe['ema3'] = ta.EMA(dataframe, timeperiod=3)

        #dataframe['ema1'] = ta.EMA(dataframe, timeperiod=1)
        dataframe['ema2'] = ta.EMA(dataframe, timeperiod=2)
        dataframe['ema3'] = ta.EMA(dataframe, timeperiod=3)
        dataframe['ema4'] = ta.EMA(dataframe, timeperiod=4)
        dataframe['ema5'] = ta.EMA(dataframe, timeperiod=5)
        dataframe['ema6'] = ta.EMA(dataframe, timeperiod=6)
        dataframe['ema7'] = ta.EMA(dataframe, timeperiod=7)
        dataframe['ema8'] = ta.EMA(dataframe, timeperiod=8)
        dataframe['ema9'] = ta.EMA(dataframe, timeperiod=9)
        dataframe['ema10'] = ta.EMA(dataframe, timeperiod=10)

        # SMA - Simple Moving Average
        #dataframe['sma'] = ta.SMA(dataframe, timeperiod=40)

        # TEMA - Triple Exponential Moving Average
        #dataframe['tema'] = ta.TEMA(dataframe, timeperiod=9)



        # Retrieve best bid and best ask
        # ------------------------------------
        # first check if dataprovider is available 
        # if self.dp:
        #     if self.dp.runmode in ('live', 'dry_run'):
        #         ob = self.dp.orderbook(metadata['pair'], 1)
        #         dataframe['best_bid'] = ob['bids'][0][0]
        #         dataframe['best_ask'] = ob['asks'][0][0]

        return dataframe

    def update_portfolio(self, type, metadata: dict):
        pair = metadata['pair']

        if type is 'buy':
            self.portfolio[pair][0] -= metadata['base_currency_quantity']
            self.portfolio[pair][1] += metadata['target_coin_quantity']
            self.free_budget[pair][1] += metadata['target_coin_quantity']
        else:
            self.portfolio[pair][0] += metadata['base_currency_quantity']
            self.portfolio[pair][1] -= metadata['target_coin_quantity']
            self.free_budget[pair][0] += metadata['base_currency_quantity']


    def make_buy_order(self, dataframe: DataFrame, metadata: dict):
        pair = metadata['pair']
        index = metadata['index']

        order = OrderItem()
        order.price = dataframe[pair].open[index]
        order.quantity = 0.001
        order.quantity_in_base_currency = order.price * order.quantity
        order.stoploss_percent = 0.03

        if order.quantity_in_base_currency <= self.free_budget[pair][0]:
            self.free_budget[pair][0] -= order.quantity_in_base_currency
            return [order]
        else:
            return []

    def make_sell_order(self, dataframe: DataFrame, metadata: dict):
        pair = metadata['pair']
        index = metadata['index']

        order = OrderItem()
        order.price = dataframe[pair].open[index]
        order.quantity = 0.001
        order.quantity_in_base_currency = order.price * order.quantity

        if order.quantity <= self.free_budget[pair][1]:
            self.free_budget[pair][1] -= order.quantity
            return [order]
        else:
            return []

    def populate_buy_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the buy signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                    (dataframe['volume'] > 0)
         #           & (dataframe['larry_k'].notna())
         #           & (dataframe['buy_target'] <= dataframe['open'])
            ),
            'buy'] = 1

        return dataframe

    def populate_sell_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Based on TA indicators, populates the sell signal for the given dataframe
        :param dataframe: DataFrame populated with indicators
        :param metadata: Additional information, like the currently traded pair
        :return: DataFrame with buy column
        """
        dataframe.loc[
            (
                (dataframe['volume'] >= 0)
            #    & (dataframe['buy'] == 0)
            ),
            'sell'] = 1
        return dataframe
