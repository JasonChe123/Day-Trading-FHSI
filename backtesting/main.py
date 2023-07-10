import datetime as dt
import os
import multiprocessing as mp
import pandas as pd
import time

from algorithm.mal_ready import MAL


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
        process = mp.Process(target=backtest, args=['MAL', start_period, end_period])
        PROCESS.append(process)
        process.start()


def backtest(strategy, data_from: dt.datetime, data_to: dt.datetime):
    print('start backtest: ', strategy, data_from, data_to)

    # build candlestrik
    pass


def get_backtest_result() -> (pd.DataFrame, pd.DataFrame):
    return pd.DataFrame(), pd.DataFrame()


if __name__ == '__main__':
    print(f"Start backtesting at {dt.datetime.now().strftime('%H:%M:%S')}")
    start_ = time.time()

    # configure params
    PROJECT_DIR = os.path.split(os.getcwd())[0]
    START_MONTH = dt.datetime(2022, 9, 1)
    END_MONTH = dt.datetime(2023, 7, 1) - dt.timedelta(days=1)
    FEE, SLIPPAGE, POINT_VALUE = 12, 30, 10
    REPORT_QUEUE = mp.Queue()
    TRADES_QUEUE = mp.Queue()
    PROCESS = []
    load_data = False
    exec_backtest = True

    # start
    if load_data:
        pass

    if exec_backtest:
        # start backtesting
        delete_reports()
        start_backtesting(START_MONTH, END_MONTH)

        # get result
        trades, monthly_report = get_backtest_result()

        # save to file
        trades.to_csv(os.path.join(PROJECT_DIR, 'backtesting', 'report', 'trade_history.csv'))
        monthly_report.to_csv(os.path.join(PROJECT_DIR, 'backtesting', 'report', 'monthly_report.csv'))
    else:
        # load report
        monthly_report = pd.read_csv(os.path.join(PROJECT_DIR, 'backtesting', 'report', 'monthly_report.csv'), index_col=0)
