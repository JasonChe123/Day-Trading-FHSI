import datetime as dt
import pandas as pd
import os


def load(project_dir: os.path):
    """
    combine individual file which contains:
      'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume'
    and save it to database
    """
    # define paths
    db_dir = os.path.join(project_dir, 'database', 'fhsi_m1')

    # create empty dataframe
    df_full = pd.DataFrame(columns=['Date', 'Time', 'Open', 'High', 'Low', 'Close', 'TotalVolume'])

    # define month symbols
    symbol_for_month = {
        'F': 1,
        'G': 2,
        'H': 3,
        'J': 4,
        'K': 5,
        'M': 6,
        'N': 7,
        'Q': 8,
        'U': 9,
        'V': 10,
        'X': 11,
        'Z': 12
    }

    # list all files in db_dir
    files = os.listdir(db_dir)

    file_list = dict()  # key: contract_year_month, value: file_name
    for file in files:
        # filter out non-csv files
        if os.path.splitext(file)[1] != '.csv':
            continue

        # identify year and month from file name
        year = int(file[4])
        month = symbol_for_month.get(file[3])
        this_year = int(str(dt.datetime.now().year)[-1])  # only concern last digit
        year += 2020 if 0 <= year <= this_year else + 2010

        # assign key, value to dictionary
        year_month = str(year).zfill(4) + str(month).zfill(2)
        file_list[year_month] = file

    # get sorted item(date) from dictionary
    sorted_date = sorted(file_list)

    # combine data (initialize rollover date first)
    rollover_date = dt.datetime.strptime('01/01/2019 09:15:00', '%d/%m/%Y %H:%M:%S')
    for date in sorted_date:
        # read file
        path = os.path.join(db_dir, file_list.get(date))
        df = pd.read_csv(path)

        # remove data before 'rollover_date'
        df['datetime'] = df.apply(
            lambda row: dt.datetime.strptime(f"{row['Date']} {row['Time']}", '%d/%m/%Y %H:%M:%S'),
            axis=1
        )
        df = df[(df['datetime'] > rollover_date)]

        # update 'rollover_date'
        rollover_date = df['datetime'].iloc[-1]

        # drop column
        df.drop(columns='datetime', inplace=True)

        # combine data
        df_full = pd.concat([df_full, df], axis=0)

    # formatting data
    df_full['x_axis'] = df_full.apply(
        lambda row: dt.datetime.strptime(f'{row["Date"]} {row["Time"]}', '%d/%m/%Y %H:%M:%S'),
        axis=1
    )
    df_full = df_full[['x_axis', 'Open', 'High', 'Low', 'Close', 'TotalVolume']]
    df_full.rename(columns={'x_axis': 'Date',
                            'TotalVolume': 'Volume'},
                   inplace=True)

    # save to database
    df_full.to_csv(os.path.join(db_dir, 'full_data', 'full_data.csv'))
