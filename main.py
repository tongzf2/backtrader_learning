# coding: utf8
# tongz2
# 2022/4/6

import backtrader as bt
import sys
import os
import datetime
import pandas as pd
import matplotlib.pyplot as plt
from backtrader.analyzers import positions
from pyfolio import create_full_tear_sheet

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False


# import matplotlib.font_manager
# matplotlib.font_manager._rebuild()


class TestStrategy(bt.Strategy):
    params = (
        ("longbars", 10),
        ("shortbars", 5)
    )
    def log(self, txt, dt=None, doprint=True):
        if doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print("{0}, {1}".format(dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.sma5 = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.longbars)
        self.sma10 = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.shortbars)
        #  Indicators for the plotting show
        bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        bt.indicators.WeightedMovingAverage(self.datas[0], period=25, subplot=True)
        bt.indicators.StochasticSlow(self.datas[0])
        bt.indicators.MACDHisto(self.datas[0])
        rsi = bt.indicators.RSI(self.datas[0])
        bt.indicators.SmoothedMovingAverage(rsi, period=10)
        bt.indicators.ATR(self.datas[0], plot=False)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log("Buy Executed, Price {0}, Cost {1}, Comm {2}".format(order.executed.price, order.executed.value,
                                                                              order.executed.comm))
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # sell
                self.log("Sell Executed, Price {0}, Cost {1}, Comm {2}".format(order.executed.price, order.executed.value,
                                                                              order.executed.comm))
        elif order.status in [order.Cancelled, order.Margin, order.Rejected]:
            self.log("order Cancelled/Margin/Rejected")
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log("OPERATION PROFIT, GROSS {0}, NET {1}".format(trade.pnl, trade.pnlcomm), doprint=False)

    def next(self):
        self.log("Close, {0}".format(self.dataclose[0]))
        if self.order:
            return
        if not self.position:
            if self.sma5 > self.sma10:  # 由于line的属性存在，两种表达方式均可
                self.order = self.buy()
                self.log("Buy Create, {0}".format(self.dataclose[0]))
        else:
            if self.sma5[0] < self.sma10[0]:  # 由于line的属性存在，两种表达方式均可
                self.order = self.sell()
                self.log("Sell Create, {0}".format(self.dataclose[0]))
        # observers 类似于止盈止损
        if self.stats.broker.value[0] < 100000.0:
            print('WHITE FLAG')
        elif self.stats.broker.value[0] > 100000000.0:
            print("TIME FOR THE VIRGIN ISLANDS.....!!!")
        self.log("DrawDown: {0}".format(self.stats.drawdown.drawdown[-1]))
        self.log("MaxDrawDown: {0}".format(self.stats.drawdown.maxdrawdown[-1]))
        # 记录
        self.mystats.write(self.data.datetime.date(0).strftime("%Y-%m-%d"))
        self.mystats.write(',%.2f' % self.stats.drawdown.drawdown[-1])
        self.mystats.write(',%.2f' % self.stats.drawdown.maxdrawdown[-1])
        self.mystats.write('\n')

    def stop(self):
        self.log("Ending Value: {0}".format(self.broker.getvalue()), doprint=True)

    def start(self):
        self.mystats = open('mystats.csv', 'w')
        self.mystats.write('datetime, drawdown, maxdrawdown\n')


if __name__ == '__main__':
    cerebro = bt.Cerebro()
    cerebro.broker.setcash(1000000.0)
    cerebro.broker.setcommission(0.005)
    cerebro.addsizer(bt.sizers.FixedSize, stake=100)
    strats = cerebro.addstrategy(TestStrategy)
    # 如果使用一系列参数，进行对比,可以使用optstra    tegy函数
    # strats = cerebro.optstrategy(TestStrategy, longbars=range(10, 31))
    # backtrader默认数据集是yahoo的股票数据
    data = bt.feeds.YahooFinanceCSVData(
        dataname="600519.SS.csv",
        fromdate=datetime.datetime(2020, 1, 1),
        todate=datetime.datetime(2022, 4, 6),
        reverse=False
    )
    # 使用yahoo数据源
    # data = bt.feeds.YahooFinanceData(
    #     dataname="MSFT",
    #     fromdate=datetime.datetime(2018, 1, 1),
    #     todate=datetime.datetime(2022, 4, 6)
    # )
    # 使用自己的数据,用数字表示数据在第几列，从0开始
    # data = bt.feeds.GenericCSVData(
    #     dataname="输入位置",
    #     datetime=2,
    #     open=3,
    #     high=4,
    #     low=5,
    #     close=6,
    #     volume=10,
    #     dtformat='%Y%m%d',
    #     fromdate=datetime.datetime(2018, 1, 1),
    #     todate=datetime.datetime(2021, 12, 31)
    # )
    # 数据特点
    # self.dataclose[0] #当日的收盘价
    # self.dataclose[-1] #昨天的收盘价
    # self.dataclose[-2] #前天的收盘价

    cerebro.adddata(data)
    print("Starting Portfolio Value: {0}".format(cerebro.broker.getvalue()))
    # Analyzer
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="mysharpe")
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name="mydrawdown")
    #cerebro.addanalyzer(bt.analyzers.TimeDrawDown, _name="mytimedrawdown")
    #cerebro.addanalyzer(bt.analyzers.Calmar, _name="mycalmar")
    cerebro.addanalyzer(bt.analyzers.Returns, _name="myreturns")
    # pyfolio
    cerebro.addanalyzer(bt.analyzers.PyFolio, _name="pyfolio")

    # observers
    cerebro.addobserver(bt.observers.Broker)
    cerebro.addobserver(bt.observers.DrawDown)
    # cerebro.addanalyzer(bt.observers.Trades)
    # cerebro.addanalyzer(bt.observers.BuySell)

    result = cerebro.run()
    strat = result[0]
    print("夏普比率：", strat.analyzers.mysharpe.get_analysis())
    print("回撤：", strat.analyzers.mydrawdown.get_analysis())
    #print("最大回撤：", strat.analyzers.mytimedrawdown.get_analysis())
    #print("卡玛比率:", strat.analyzers.mycalmar.get_analysis())
    print("收益:", strat.analyzers.myreturns.get_analysis())
    print("Final Portfolio Value: {0}".format(cerebro.broker.getvalue()))

    # # pyfolio
    # pyfoliozer = strat.analyzers.getbyname("pyfolio")
    # returns, positions, transactions, gross_lev = pyfoliozer.get_pf_items()
    # import pyfolio as pf
    # pf.create_full_tear_sheet(
    #     returns,
    #     positions=positions,
    #     transactions=transactions,
    #     live_start_date="2020-01-31"
    # )
    #cerebro.plot()
    # 时间范围
    cerebro.plot(start=datetime.date(2021, 1, 1), end=datetime.date(2021, 12, 31))
    # bt.analyzers.AnnualReturn()
    # bt.analyzers.TimeReturn()
    # bt.analyzers.Returns()