import calendar
import datetime as dt
import holidays
import logging


def check_is_holiday(date_given: dt.date) -> bool:
    """
    return true if the date given is public holiday, Sat or Sun (Hong Kong)
    """
    # check argument type
    if not isinstance(date_given, dt.date):
        logging.error("Wrong argument type, only datetime.date is accepted.")
        return False

    # checking
    if date_given.isoweekday() in (6, 7) or date_given in holidays.HongKong():
        return True

    return False


def get_contract_year_and_month() -> (str, str):
    """
    return: contract year, contract month
    """
    def get_last_trading_day_in_this_month(last_days: int) -> int:
        # get total days in current month
        weekday, num_of_days = calendar.monthrange(dt.date.today().year, dt.date.today().month)
        days = list(range(1, num_of_days + 1))

        # count trading days from the end of the month
        trading_days = 0
        for i in reversed(days):
            if check_is_holiday(dt.date.today().replace(day=i)):
                continue
            else:
                trading_days += 1
            if trading_days == last_days or i == days[0]:
                return i

    current_month = dt.date.today().month
    next_month = 1 if current_month == 12 else current_month + 1
    contract_year = str(dt.date.today().year)[-2:]
    contract_month = str(current_month).zfill(2)

    # check if today is 4 days earlier from the end
    if dt.date.today().day >= get_last_trading_day_in_this_month(4):
        contract_month = str(next_month).zfill(2)

        # check if today is the last month
        if current_month == 12 and int(contract_month) == 1:
            contract_year = str(dt.date.today().year + 1)[-2:]

    return contract_year, contract_month
