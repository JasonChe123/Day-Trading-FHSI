import datetime as dt
import os
import multiprocessing as mp
import numpy as np
import pandas as pd
import time
from typing import Type

from algorithm.template import AlgoTemplate
from algorithm.mal_ready import MAL
import charts
import load_data


class BackTestEngine:
    def __init__(self,
                 strategy: Type[AlgoTemplate],
                 chart: object,
                 data: pd.DataFrame,
                 symbol: str = 'HK.HSImain',
                 start_date: dt.datetime = dt.datetime(2010, 1, 1),
                 end_date: dt.datetime = dt.datetime.now()):
        """
        perform backtesting, generate report
        :param strategy: AlgoTemplate class
        :param data: dataframe (columns: 'Date' 'Open' 'High' 'Low' 'Close' 'Volume')
        :param symbol: trading symbol/ code
        :param start_date:
        :param end_date:
        """
        self.engine = 'backtest'
        self.strategy = strategy(self, symbol)
        self.strategy.kline_daily = pd.read_csv(
            os.path.join(PROJECT_DIR, 'database', 'fhsi_daily_kline.csv'),
            index_col=0
        )
        self.chart = chart
        self.data = data
        self.commission = FEES / POINT_VALUE  # in terms of point
        self.slippage = SLIPPAGE / POINT_VALUE  # in terms of point
        self.point_value = POINT_VALUE
        self.backtest_data = pd.DataFrame()
        self.df_trd_jrl = pd.DataFrame(columns=['time_key', 'side', 'qty', 'price', 'remark'])
        self.symbol = symbol
        self.start_date = start_date.replace(hour=9, minute=15)
        self.end_date = end_date.replace(hour=3, minute=0) + dt.timedelta(days=1)

    def start_testing_strategy(self):
        """
        start backtesting for the specified period (self.start_date to self.end_date)
        1. apply indicators to the chart and visualize them
        2. checking conditions bar by bar
        :return: None
        """
        # extract data from start_date to end_date
        data = self.data.copy()
        data['time_key'] = pd.to_datetime(data['time_key'])
        data = data.loc[(data['time_key'] >= self.start_date) &
                        (data['time_key'] <= self.end_date)]

        # apply necessary indicators
        data.reset_index(inplace=True)
        self.strategy.apply_indicators(kline=data)

        # add ema_fast to the chart
        x_data = self.strategy.ema_fast.index
        y_data = self.strategy.ema_fast.tolist()
        self.chart.add_ta(x_data=x_data, y_data=y_data, name='EMA Fast', width=1, type_='solid', color='red')

        # add ema_slow to the chart
        x_data = self.strategy.ema_slow.index
        y_data = self.strategy.ema_slow.tolist()
        self.chart.add_ta(x_data=x_data, y_data=y_data, name='EMA Slow', width=1, type_='solid', color='green')

        # add bollinger bands to the chart
        x_data = self.strategy.bb_top.index
        y_data_top = self.strategy.bb_top.tolist()
        y_data_bot = self.strategy.bb_bot.tolist()
        y_data_mid = self.strategy.bb_mid.tolist()
        self.chart.add_ta(x_data=x_data, y_data=y_data_top, name='BBands', width=1, type_='dashed', color='grey')
        self.chart.add_ta(x_data=x_data, y_data=y_data_bot, name='BBands', width=1, type_='dashed', color='grey')
        self.chart.add_ta(x_data=x_data, y_data=y_data_mid, name='BBands', width=1, type_='dashed', color='grey')

        # add adx
        x_data = self.data['time_key'].tolist()
        y_data = self.strategy.adx.tolist()
        self.chart.add_ta(x_data=x_data, y_data=y_data, name='ADX', width=1, type_='solid', color='black', is_subchart=True)

        # start feeding data
        self.backtest_data = data
        for i in range(500, self.backtest_data.shape[0], 1):
            self.strategy.update_kline(kline='foo', index=i)

    def get_monthly_report(self):

        def write_to_report(df: pd.DataFrame, pnl: int, trd_qty: int) -> None:
            """
            write value to the last row of original dataframe
            :param df: report dataframe
            :param pnl: profit/loss in point
            :param trd_qty: traded quantity
            :return: None
            """
            i = df.index[-1]
            df.loc[i, 'Profit/Loss'] = int(pnl*self.point_value - (self.slippage + self.commission)*trd_qty*self.point_value)
            df.loc[i, 'Traded Qty'] = trd_qty
            df.loc[i, 'Commission'] = int(self.commission*trd_qty*self.point_value)
            df.loc[i, 'Slippage'] = self.slippage*trd_qty*self.point_value

        def processing(df: pd.DataFrame) -> pd.DataFrame:
            """
            generate report (Period, Profit/Loss, Traded Qty, Commission, Slippage)
            on original dataframe
            :param df: trade journal
            :return: report
            """
            # initialize variables
            if df.empty:
                return df

            curr_month = df.at[0, 'time_key'].month
            pnl = trd_qty = 0
            new_row = {'Period': 0, 'Profit/Loss': 0, 'Traded Qty': 0, 'Commission': 0, 'Slippage': 0}
            df_report = pd.DataFrame(columns=new_row.keys())
            df_report.loc[len(df_report)] = new_row
            df_report['Period'].iloc[-1] = dt.datetime.strftime(df.at[0, 'time_key'], '%Y-%b')

            # generating report
            for i, row in df.iterrows():
                # new month
                if row['time_key'].month != curr_month and row['time_key'].hour > 3:
                    curr_month = row['time_key'].month
                    write_to_report(df_report, pnl, trd_qty)
                    df_report.loc[len(df_report)] = new_row  # add new row
                    df_report.loc[df_report.index[-1], 'Period'] = dt.datetime.strftime(df.at[i, 'time_key'], '%Y-%b')
                    pnl = trd_qty = 0

                # sum up
                pnl += row['cost_price']
                trd_qty += row['qty']

            # finish, add last month
            write_to_report(df_report, pnl, trd_qty)

            return df_report

        # initialize dataframe
        df = self.df_trd_jrl.copy()
        df['cost_price'] = df.apply(
            lambda row: row['price']*row['qty'] if row['side'] == 'SELL' else row['price']*row['qty']*-1,
            axis=1
        )

        return processing(df)

    def add_trades_to_chart(self, chart):
        """
        add trade historical lines to candlestick
        :param chart: Kline()
        :return: None
        """
        positions = []
        for i, row in self.df_trd_jrl.iterrows():
            time_key = dt.datetime.strftime(row['time_key'], '%Y-%m-%d %H:%M:%S')
            signal = row['remark'].lstrip(self.strategy.name).lstrip('-')
            # open position
            if signal[:2] in ('LE', 'SE'):
                pos_detail = {'time_key': time_key,
                              'side': row['side'],
                              'price': row['price'],
                              'qty': row['qty'],
                              'remark': row['remark']
                              }
                positions.append(pos_detail)
            # todo: assume closing all positions
            # close position -> add line to chart
            else:
                row['time_key'] = dt.datetime.strftime(row['time_key'], '%Y-%m-%d %H:%M:%S')
                row['remark'] = row['remark'].lstrip(self.strategy.name).lstrip('-')
                for pos in positions:
                    pos['remark'] = pos['remark'].lstrip(self.strategy.name).lstrip('-')
                    chart.add_trading_line(entry=pos, exit_=row, name=self.strategy.name, comm=self.commission,
                                           slippage=self.slippage, point_value=self.point_value)
                positions = []

    # -------------------------------------------------------------------------
    """ callbacks methods from algo strategy """
    # -------------------------------------------------------------------------
    def fire_trade(self, side: str, qty: int, remark: str, order_type: str, index: int = 0) -> None:
        """
        simulate trade and assign to the self.df_trd_jrl
        :param side: 'BUY'/'SELL
        :param qty: execute quantity of contracts
        :param remark: trade's remark, usually a signal name
        :param order_type: 'LIMIT'/'AUCTION'/... always 'MARKET'
        :param index: current index of the kline, used to identify 'time_key', only used for backtesting
        :return: None
        """
        time_key = self.backtest_data['time_key'].iloc[index + 1]
        price = self.backtest_data['open'].iloc[index + 1]
        self.strategy.update_backtest_params(side=side, qty=qty, price=price)

        # update trade journal
        new_row = {'time_key': time_key, 'side': side, 'qty': qty, 'price': price, 'remark': remark}
        self.df_trd_jrl.loc[len(self.df_trd_jrl)] = new_row


def delete_reports():
    """
    delete all files in 'report' directory before a new backtesting
    """
    directory = os.path.join(PROJECT_DIR, 'backtesting', 'report')
    for file in os.listdir(directory):
        os.remove(os.path.join(directory, file))


def start_backtesting(start_date: dt.datetime, end_date: dt.datetime):
    # get cpus
    nos_of_cpu = mp.cpu_count()
    days_per_cpu = (end_date - start_date).days // nos_of_cpu

    # assign backtest period to cpus
    for cpu in range(nos_of_cpu):
        start_period = start_date + dt.timedelta(days=cpu*days_per_cpu)
        if cpu == range(nos_of_cpu)[-1]:
            end_period = end_date
        else:
            end_period = start_period + dt.timedelta(days=days_per_cpu - 1)
        process = mp.Process(target=backtest, args=[MAL, start_period, end_period])
        PROCESS.append(process)
        process.start()


def backtest(strategy: MAL, data_from: dt.datetime, data_to: dt.datetime):
    print(f"Backtesting {strategy.name} from {data_from.strftime('%Y-%m-%d')} to {data_to.strftime('%Y-%m-%d')}")

    # build candlestick
    chart = charts.CandleStick(project_dir=PROJECT_DIR, from_=data_from, to_=data_to)
    if chart.fhsi_chart_data.empty:
        return

    # start backtesting
    data = chart.get_chart_data()
    cols = {'Date': 'time_key',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'}
    data = data.rename(columns=cols)  # match column names to ibapi
    back_test = BackTestEngine(strategy=strategy, chart=chart, data=data, start_date=data_from, end_date=data_to)
    back_test.start_testing_strategy()
    back_test.add_trades_to_chart(chart)

    # output report, trades and chart
    REPORT_QUEUE.put(back_test.get_monthly_report())
    TRADES_QUEUE.put(back_test.df_trd_jrl.copy())
    chart.export_chart(
        file_name=f'backtest_{back_test.strategy.name}_{data_from.strftime("%y%m")}_to_{data_to.strftime("%y%m")}.html')

    print(f"Backtesting {strategy.name} from {data_from.strftime('%Y-%m-%d')} to {data_to.strftime('%Y-%m-%d')} finished.")


def get_backtest_result() -> (pd.DataFrame, pd.DataFrame):
    """
    get trades and report from multiprocessing
    :return: trades, report
    """
    trades, report = pd.DataFrame(), pd.DataFrame()
    trade_count = report_count = 0

    # get trades and report from QUEUE
    while True:
        if TRADES_QUEUE.qsize() != 0:
            trades = pd.concat([trades, TRADES_QUEUE.get()], axis=0, ignore_index=True)
            trade_count += 1
        if REPORT_QUEUE.qsize() != 0:
            report = pd.concat([report, REPORT_QUEUE.get()], axis=0, ignore_index=True)
            report_count += 1
        if trade_count == report_count == mp.cpu_count():
            break

    # wait for all processes finished
    report = report.groupby(['Period'], as_index=False).sum()
    [proc.join() for proc in PROCESS]

    # sort data
    trades.sort_values('time_key', inplace=True, ignore_index=True)
    report['sort_value'] = report.apply(lambda col: dt.datetime.strptime(col['Period'], '%Y-%b'), axis=1)
    report.sort_values('sort_value', inplace=True, ignore_index=True)
    report.drop(columns=['sort_value', 'time_key', 'side', 'qty', 'price', 'remark', 'cost_price'], inplace=True)
    report.loc['Total'] = report.sum(numeric_only=True)

    return trades, report


def generate_detail_report(path_: os.path) -> pd.DataFrame | type:
    """
    generate detail report with equity curve
    :param path_: path of trades history in csv format
    :return: detail report
    """
    # configure params
    df = pd.read_csv(path_, index_col=[0])
    df['fees'] = df['qty'] * FEES
    df['slippage'] = df['qty'] * SLIPPAGE
    df['cost_price'] = (df['price'] * df['qty']).where(df['side'] == 'SELL', df['price'] * -df['qty'])

    # calculate profit/loss
    df['pnl'] = 0
    df['accu_pnl'] = 0
    pnl = accu_pnl = 0
    for i, row in df.iterrows():
        amount = row['cost_price'] * 10 - row['slippage'] - row['fees']
        accu_pnl += amount
        if row['side'] == 'SELL':
            pnl += amount
            df.at[i, 'pnl'] = pnl
            pnl = 0
            df.at[i, 'accu_pnl'] = accu_pnl
        else:
            pnl += amount
            df.at[i, 'pnl'] = None
            df.at[i, 'accu_pnl'] = None

    # plot equity curve
    from_ = dt.datetime.strptime(df['time_key'].iloc[0], '%Y-%m-%d %H:%M:%S')
    from_ = dt.datetime.strftime(from_, '%Y-%m-%d')
    to_ = dt.datetime.strptime(df['time_key'].iloc[-1], '%Y-%m-%d %H:%M:%S')
    to_ = dt.datetime.strftime(to_, '%Y-%m-%d')
    line_chart = charts.LineChart(x_data=df['time_key'].tolist(), y_data=df['accu_pnl'],
                                  title='Equity Curve', sub_title=f'From {from_} to {to_}')

    # add drawdown curve
    y_data = []
    drawdown = get_drawdown(df['accu_pnl'])
    for value in df['accu_pnl']:
        y_data.append(value) if pd.isna(value) else y_data.append(drawdown.pop(0))
    line_chart.add_drawdown(df['time_key'].tolist(), y_data=y_data, name='DrawDown')

    return df, line_chart


def get_drawdown(series: pd.Series):
    value = series.dropna().reset_index(drop=True)
    dd = [0]
    for i in value.index[1:]:
        diff = value[i] - value[i - 1]
        dd.append(dd[-1] + diff) if diff < 0 else dd.append(min(0, dd[-1] + diff))

    return dd


def generate_overview(detail_report: pd.DataFrame, line_chart: type) -> pd.DataFrame:
    df_overview = pd.DataFrame(columns=['Profit/Loss', 'Win Rate', 'Largest Winning Trade', 'Largest Losing Trade',
                                        'Largest Recovery Time(Days)', 'Recovery From', 'Recovery To',
                                        'Traded Contracts', 'Daily Traded Avg', 'Commission', 'Slippage',
                                        'Max DrawDown', 'Max RunUp', 'Profit Factor', 'Sharpe Ratio',
                                        'Return/Risk Ratio'])

    # get profit/loss
    pnl = detail_report['pnl'].sum()
    df_overview.loc[0, 'Profit/Loss'] = int(pnl)

    # get win rate
    df_win = detail_report[detail_report['pnl'] > 0]
    df_lose = detail_report[detail_report['pnl'] < 0]
    win_rate = round(df_win.shape[0] / (df_win.shape[0] + df_lose.shape[0]), 2)
    df_overview.loc[0, 'Win Rate'] = win_rate

    # get the largest winning trade
    largest_winning_trade = detail_report.iloc[[detail_report['pnl'].idxmax()]].reset_index()
    df_overview.loc[0, 'Largest Winning Trade'] = int(largest_winning_trade.at[0, 'pnl'])

    # get the largest losing trade
    largest_losing_trade = detail_report.iloc[[detail_report['pnl'].idxmin()]].reset_index()
    df_overview.loc[0, 'Largest Losing Trade'] = int(largest_losing_trade.at[0, 'pnl'])

    # get recovery time
    df_overview.loc[0, 'Largest Recovery Time(Days)'] = line_chart.recovery_time
    df_overview.loc[0, 'Recovery From'] = line_chart.recovery_from
    df_overview.loc[0, 'Recovery To'] = line_chart.recovery_to

    # get traded contracts, commissions, slippage
    total_traded_qty = detail_report['qty'].sum()
    df_overview.loc[0, 'Traded Contracts'] = total_traded_qty
    df_overview.loc[0, 'Commission'] = detail_report['fees'].sum()
    df_overview.loc[0, 'Slippage'] = detail_report['slippage'].sum()

    # count average daily trade
    last_day = dt.datetime.strptime(detail_report['time_key'].iloc[-1], '%Y-%m-%d %H:%M:%S')
    first_day = dt.datetime.strptime(detail_report['time_key'].iloc[0], '%Y-%m-%d %H:%M:%S')
    days_diff = (last_day - first_day).days
    df_overview.loc[0, 'Daily Traded Avg'] = round(total_traded_qty/days_diff, 2)

    # get MDD
    mdd = get_mdd(detail_report['accu_pnl'].dropna().reset_index(drop=True))
    df_overview.loc[0, 'Max DrawDown'] = int(mdd)

    # get max run_up
    mru = get_max_run_up(detail_report['accu_pnl'].dropna().reset_index(drop=True))
    df_overview.loc[0, 'Max RunUp'] = int(mru)

    # get profit-factor
    profit_trade = detail_report[detail_report['pnl'] > 0]['pnl'].sum()
    loss_trade = abs(detail_report[detail_report['pnl'] < 0]['pnl'].sum())
    df_overview.loc[0, 'Profit Factor'] = round(profit_trade / max(1, loss_trade), 2)

    # get sharpe ratio
    df = detail_report['pnl'].dropna().pct_change()
    average_return = df.mean()
    std_dev = df.std()
    trading_days_per_year = 252
    sharpe_ratio = (average_return * np.sqrt(trading_days_per_year)) / std_dev
    df_overview['Sharpe Ratio'] = round(sharpe_ratio, 2)

    # get 'risk/return' ratio
    df_overview['Return/Risk Ratio'] = round(pnl/-mdd, 2)

    # formatting
    df = df_overview.T
    df.rename(columns={0: 'MAL'}, inplace=True)

    return df


def get_mdd(value: pd.Series):
    return min(get_drawdown(value))


def get_max_run_up(value: pd.Series):
    ru = [value[0]]
    for i in value.index[1:]:
        diff = value[i] - value[i - 1]
        ru.append(ru[-1] + diff) if diff > 0 else ru.append(max(0, ru[-1] + diff))

    return max(ru)


if __name__ == '__main__':
    print(f"Start backtesting at {dt.datetime.now().strftime('%H:%M:%S')}")
    start_ = time.time()

    # configure params
    PROJECT_DIR = os.path.split(os.getcwd())[0]
    REPORT_DIR = os.path.join(PROJECT_DIR, 'backtesting', 'report')
    START_MONTH = dt.datetime(2019, 1, 1)
    END_MONTH = dt.datetime(2023, 2, 1) - dt.timedelta(days=1)
    FEES, SLIPPAGE, POINT_VALUE = 12, 30, 10
    REPORT_QUEUE = mp.Queue()
    TRADES_QUEUE = mp.Queue()
    PROCESS = []
    is_load_data = False
    exec_backtest = True

    # start
    if is_load_data:
        load_data.load(PROJECT_DIR)

    if exec_backtest:
        # start backtesting
        delete_reports()
        start_backtesting(START_MONTH, END_MONTH)

        # get result
        trades, monthly_report = get_backtest_result()

        # save to file
        trades.to_csv(os.path.join(REPORT_DIR, 'trade_history.csv'))
        monthly_report.to_csv(os.path.join(REPORT_DIR, 'monthly_report.csv'))
    else:
        # load report
        monthly_report = pd.read_csv(os.path.join(PROJECT_DIR, 'backtesting', 'report', 'monthly_report.csv'), index_col=0)

    # generate yearly report
    df = monthly_report.copy()
    df = df[:-1]  # drop the last row "Total"
    df['Year'] = df.apply(lambda col: dt.datetime.strptime(col['Period'], '%Y-%b').year, axis=1)
    df.drop(columns=['Period'], inplace=True)
    yearly_report = df.groupby(['Year']).sum()
    yearly_report.to_csv(os.path.join(REPORT_DIR, 'yearly_report.csv'))

    # generate detail report
    detail_report, line_chart = generate_detail_report(
        os.path.join(REPORT_DIR, 'trade_history.csv')
    )

    # overview
    report_overview = generate_overview(detail_report, line_chart)
    report_overview.to_csv(os.path.join(REPORT_DIR, 'report_overview.csv'))

    # add information to Line chart
    monthly_report.at['Total', 'Period'] = 'Total'
    monthly_report.set_index('Period', inplace=True)
    line_chart.add_monthly_report(monthly_report)
    line_chart.add_yearly_report(yearly_report)
    line_chart.add_overview_text(report_overview)
    line_chart.export_chart(path=os.path.join(REPORT_DIR, 'equity_curve.html'))

    print(f"\nFinished, {round(time.time() - start_, 2)} seconds used.")