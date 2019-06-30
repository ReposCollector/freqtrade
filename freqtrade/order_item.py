from enum import Enum
from typing import Dict, List, NamedTuple, Tuple


class SignalType(Enum):
    """
    Enum to distinguish between buy and sell signals
    """
    BUY = "buy"
    SELL = "sell"


class SellType(Enum):
    """
    Enum to distinguish between sell reasons
    """
    ROI = "roi"
    STOP_LOSS = "stop_loss"
    STOPLOSS_ON_EXCHANGE = "stoploss_on_exchange"
    TRAILING_STOP_LOSS = "trailing_stop_loss"
    SELL_SIGNAL = "sell_signal"
    FORCE_SELL = "force_sell"
    TIMEOUT = "timeout"
    NONE = ""


class SellCheckTuple(NamedTuple):
    """
    NamedTuple for Sell type + reason
    """
    sell_flag: bool
    sell_type: SellType


class OrderItem:
    SELL_FEE = 0.005
    BUY_FEE = 0.005

    def __init__(self):
        self.buy_price = -1
        self.buy_quantity = -1
        self.buy_quantity_in_base_currency = -1
        self.buy_processed_date = -1
        self.buy_index = -1

        self.stoploss_percent = -1
        self.timeout_seconds = -1              # in minutes
        self.take_profit_percent = -1

        self.sell_price = -1


    def has_sell_plan(self):
        return  (self.stoploss_percent != -1 or self.timeout_seconds != -1 or self.take_profit_percent != -1)

    def has_to_sell(self, row):
        if (self.has_sell_plan() is False):
            return SellType.NONE

        if self.stoploss_percent != -1:
            stoploss_price = self.buy_price * (1 - self.stoploss_percent)
            if stoploss_price >= row.low:
                self.sell_price = stoploss_price
                return SellType.STOP_LOSS

        if self.timeout_seconds != -1:
            date_passed = row.date - self.buy_processed_date
            if self.timeout_seconds <= date_passed.total_seconds():
                self.sell_price = row.open
                return SellType.TIMEOUT

        if self.take_profit_percent != -1:
            take_profit_price = self.buy_price * (1 + self.take_profit_percent)
            if take_profit_price <= row.high:
                self.sell_price = take_profit_price
                return SellType.ROI

        return SellType.NONE

    def calc_buy_net(self):
        buy_trade = self.buy_quantity * self.buy_price
        buy_fees = buy_trade * OrderItem.BUY_FEE
        return float(buy_trade + buy_fees)

    def calc_sell_net(self):
        sell_trade = self.buy_quantity * self.sell_price
        sell_fees = sell_trade * OrderItem.SELL_FEE
        return float(sell_trade - sell_fees)

    def calc_profit_percent(self):
        open_trade_price = self.calc_buy_net()
        close_trade_price = self.calc_sell_net()
        return (close_trade_price / open_trade_price) - 1

    def calc_profit(self):
        open_trade_price = self.calc_buy_net()
        close_trade_price = self.calc_sell_net()
        return (close_trade_price - open_trade_price)