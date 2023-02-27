# This code is primarily support functions intended to help the user and to assist other functions

import yfinance as yf
from datetime import timedelta


# set the date ranges to focus on 5 weekdays, based on a given input
# the test data will be from the input date forward, historical data will be from the input date backwards
# provide: start_date - use the date function from datetime
# returns: list with end_date (five business days from start), hist_start and hist_end (historical data start/end dates)
def date_ranges(start_date):
    if start_date.weekday() == 0:
        end_date = start_date + timedelta(days=5)
        hist_end = start_date - timedelta(days=2)
        hist_start = start_date - timedelta(days=8)
    elif start_date.weekday() == 5:
        end_date = start_date + timedelta(days=7)
        hist_end = start_date
        hist_start = start_date - timedelta(days=5)
    elif start_date.weekday() == 6:
        end_date = start_date + timedelta(days=6)
        hist_end = start_date - timedelta(days=1)
        hist_start = start_date - timedelta(days=7)
    else:
        end_date = start_date + timedelta(days=7)
        hist_end = start_date
        hist_start = start_date - timedelta(days=7)
    return [end_date, hist_start, hist_end]


# prepare historical data from stock listing
# pull the target stock's data over five minute intervals for a given date range
# add a column for 'average' of that 5 minute interval based on the open and close price and remove extra columns
# provide: target_stock (provide the ticker, e.g. 'MSFT'), start_date and end_date to pull data for
# return: prepped_data pulled from yahoo finance at 5 minute intervals for a date range, with prices averaged out
def prep_data(target_stock, start_date, end_date):
    prepped_data = yf.Ticker(target_stock).history(interval='5m', start=start_date, end=end_date)
    prepped_data = prepped_data[['Open', 'Close']]
    prepped_data['Average'] = (prepped_data['Open'] + prepped_data['Close']) / 2
    return prepped_data


# recommend target sell/buy prices for a stock based on standard deviation from average over a given date range
# you can use a factor for std deviation other than 1 (ex target .8 of a std deviation instead of 1)
# provide: target_stock (ticker e.g. 'MSFT'), start_date to use as a starting point to pull historical data,
#           and std_use to provide a factor of standard deviation to use to determine prices
# returns: list of recommended purchse price and sell price
def recommend_points(target_stock, start_date, std_use):
    date_list = date_ranges(start_date)
    hist_start = date_list[1]
    hist_end = date_list[2]

    # pull historical data for last 5 days at 5 minute increments, determine recommended sell/buy price
    historical_data = prep_data(target_stock, hist_start, hist_end)
    baseline_price = historical_data['Average'].mean()
    standard_deviation = historical_data['Average'].std()*std_use
    buy_price = baseline_price - standard_deviation
    sell_price = baseline_price + standard_deviation
    return [buy_price, sell_price]


# recommend target sell/buy points for a stock based on only one day of data as opposed to five days
# again you can use whatever factor of standard deviation you want
# provide: target_stock (ticker e.g. 'MSFT'), start_date to use as a starting point to pull historical data,
#           and std_use to provide a factor of standard deviation to use to determine prices
# returns: list of recommended purchse price and sell price
def recommend_points_one_day(target_stock, start_date, std_use):
    # pull the prior business day based on the provided start date
    if start_date.weekday() == 0:
        hist_start = start_date - timedelta(days=3)
    else:
        hist_start = start_date - timedelta(days=1)

    # pull historical data for last day at 5 minute increments, determine recommended sell/buy price
    historical_data = prep_data(target_stock, hist_start, start_date)
    baseline_price = historical_data['Average'].mean()
    standard_deviation = historical_data['Average'].std()*std_use
    buy_price = baseline_price - standard_deviation
    sell_price = baseline_price + standard_deviation
    return [buy_price, sell_price]
