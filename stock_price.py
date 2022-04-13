import pandas as pd
import numpy as np
import tushare as ts
import backtrader as bt
from datetime import date
from datetime import datetime
import matplotlib.pyplot as plt

from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']
mpl.rcParams['axes.unicode_minus'] = False


def get_data(code, start='20150101'):
    today = date.today()
    end = today.strftime('%Y%m%d')
    pro = ts.pro_api()
    pro = ts.pro_api('958222b253447a054ab4de6381295a0f525d29d2f4aabb2b5c1c46c8')
    df = pro.daily(ts_code=code, start_date=start, end_date=end)
    df['openinterest'] = 0
    df.index = pd.to_datetime(df['trade_date'])
    df = df.sort_index(axis=0)
    plot_stock(df, code, start, end)
    return df


def plot_stock(data, code, start, end):
    data['close'].plot(figsize=(14, 6), color='r')
    plt.title(code+start+end)
    plt.annotate(f'期间累计涨幅:{(data["close"][-1]/data["close"][0]-1)*100:.2f}%', xy=(data.index[-150], data.close.mean()),
             xytext=(data.index[-500], data["close"].min()), bbox=dict(boxstyle='round,pad=0.5',
            fc='yellow', alpha=0.5), arrowprops=dict(facecolor='green', shrink=0.05), fontsize=12)
    plt.show()


if __name__ == '__main__':
    df = get_data('600519.SH')
    print(df.columns)
    print(df)
