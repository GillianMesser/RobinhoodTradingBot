# This primarily contains functions used for testing a particular stock to see how compatible it is with this logic

from datetime import timedelta, date
import numpy as np
from support_functions import prep_data, recommend_points


# TEST FUNCTIONS to help determine if a stock might be a good option
# ==============================================================================================================
# look at a particular stock and report what would have been bought and sold over a one-day period
# with a given start date, the following five days will be the 'test' range you would buy/sell over
# you can also provide a target price to sell at or buy at, as well as how much to spend on each purchase
# if price drops below the target buy price, a buy would be triggered the moment price starts to rise again
# once a buy is triggered, it will start looking to sell (it will not buy multiple times in a row)
# the sell will trigger if price goes above your target sell price the moment price starts to fall again
# it'll use 5m intervals and that will only work for the last 60ish days, so it's not exact but is a good reference
# returns amount bought, sold, count (count of full cycle transactions bought/sold), profit, holding (stock remaining)
def analyze_stock(target_stock, start_date, buy_price, sell_price, spend):
    end_date = start_date + timedelta(days=1)

    # break out the data set into factors to help determine when to buy and when to sell
    test_data = prep_data(target_stock, start_date, end_date)
    test_data['Buy'] = np.where(test_data['Average'] <= buy_price, 'buy', '')
    test_data['Sell'] = np.where(test_data['Average'] >= sell_price, 'sell', '')
    test_data['shifted'] = test_data['Average'].shift(1)
    test_data['Rise'] = np.where(test_data['shifted'] < test_data['Average'], 'rise', '')
    test_data['Drop'] = np.where(test_data['shifted'] > test_data['Average'], 'drop', '')
    test_data['Actual Buy'] = np.where((test_data['Rise'] == 'rise') & (test_data['Buy'] == 'buy'),
                                       test_data['Average'], '0')
    test_data['Actual Sell'] = np.where((test_data['Drop'] == 'drop') & (test_data['Sell'] == 'sell'),
                                        test_data['Average'], '0')

    # create a record of actual purchase/sell points
    flag = 'buy'
    flag_column = 'Actual Buy'
    record = list()
    for index, row in test_data.iterrows():
        if float(row[flag_column]) > 0:
            record.append([row[flag_column], flag])
            if flag == 'buy':
                flag = 'sell'
                flag_column = 'Actual Sell'
            else:
                flag = 'buy'
                flag_column = 'Actual Buy'

    # if we bought something, check the end of day close price to see if we should sell it
    if len(record) != 0:
        if flag == 'sell':
            bought_at = float(record[int(len(record) - 1)][0])
            close_price = float(test_data['Average'].iat[-1])
            if bought_at < close_price:
                record.append([close_price, 'sell'])

    # if record is empty, no buys made so no buy/sell data to report
    # otherwise, figure out buy/sell/profit data
    if len(record) == 0:
        bought = 0
        sold = 0
        count = 0
        profit = 0
        holding = 0
    else:
        bought = 0
        sold = 0
        count = 0
        percent_holding = 0
        for item in range(len(record)):
            if record[item][1] == 'buy':
                bought = bought + spend
                percent_holding = spend / float(record[item][0])
            elif record[item][1] == 'sell':
                sold = sold + (percent_holding * float(record[item][0]))
                count = count + 1

        profit = sold - bought
        if (count * spend) < bought:
            holding = percent_holding
            profit = profit + spend
        else:
            holding = 0

    return [bought, sold, count, profit, holding]


# for a given stock, pull its recommend prices and use those to analyze the stock using analyze_stock
# user provides the start date, target stock, spend amount, and standard deviation factor
# returns the listed info from analyze_stock function
def full_check(start_date, target_stock, std_use, max_spend):
    prices = recommend_points(target_stock, start_date, std_use)
    info = analyze_stock(target_stock, start_date, prices[0], prices[1], max_spend)
    return info


# analyze a stock using full_check for the last 'x' days
# this will run a series of checks on the target stock for the past 'x' days to get a range of reference data
# the totals bought/sold/transactions/profit/stock remaining will be displayed at the end
def test_x_days(target_stock, std_use, max_spend, day_count):
    start_date = date.today()
    bought = 0
    sold = 0
    profit = 0
    count = 0
    holding = 0
    for n in list(range(0, day_count)):
        start_date = start_date - timedelta(days=1)
        if not start_date.weekday() == 5 and not start_date.weekday() == 6:
            info = full_check(start_date, target_stock, std_use, max_spend)
            bought = bought + info[0]
            sold = sold + info[1]
            count = count + info[2]
            profit = profit + info[3]
            holding = holding + info[4]
    print(f'Analysis of {target_stock} over the last {day_count} days:')
    print(f'Bought ${bought} in total, sold ${sold} in total, for {count} complete buy/sell transactions.')
    print(f'Total profit was ${profit} with {holding} shares still in holding')
