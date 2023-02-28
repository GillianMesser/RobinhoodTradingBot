# This is an alternate approach to the logic used to determine when to buy and sell
# With this approach, the code will buy and sell every dip as opposed to targeting specific buy/sell prices.
# Note that stock will be bought, then sold.  The code will not buy multiple times in a row.
# Stock remaining at the end of the day (unsold) will be left for the user to decide what to do with it.

import robin_stocks.robinhood as rs
from time import sleep
from datetime import datetime

# USER INPUTS
# Change these values
# =================================================================================================================
# MFA is assumed to be active/on for your Robinhood account.  If not, you'll need to turn it on.
# If you cannot pull a single fixed MFA code or would rather Robinhood contact you with single-use codes, you will
# be prompted to provide that code in the terminal when the system attempts to log in.
# If you need help determining sell/buy price, see support_functions.py for recommend_points functionality
username = 'example@email.com'      # Robinhood username (usually your login email)
password = 'Password123'            # Robinhood password
mfa = '123456'                      # MFA code (if MFA turned on - user will be prompted in terminal if error)
target_stock = 'MSFT'               # Target stock ticker
spend = 1                           # Dollar amount you will spend on each purchase (minimum of $1)

# time range is set to 9:05am to 4:55pm; you can change this to whatever trade window you want
current_time = datetime.now()
start_time = current_time.replace(hour=9, minute=5, second=0, microsecond=0)
end_time = current_time.now().replace(hour=16, minute=55, second=0, microsecond=0)

# PRE-CHECKS
# =================================================================================================================
# Check to make sure the user input is correct
proceed = None
while proceed not in ('yes', 'no'):
    proceed = input(f'You are targeting {target_stock} to be purchased and sold at every dip/rise in ${spend} increments.  Is this correct (yes or no)? ')
    if proceed == 'no':
        exit('The code has ended, adjust your target stock info and try again.')
    elif proceed == 'yes':
        break
    else:
        print(f'You must enter either yes or no.')

# Check to make sure spend price is valid.
if spend < 1:
    print(f'Your target spend amount was provided as {spend}.  The minimum spend amount allowed for fractional trading is $1, please adjust your spend amount and try again.')
    exit('The code has ended, adjust your spend amount to be at least $1.')


# PRIMARY CODE
# =================================================================================================================
# log in (may prompt you for an MFA if required and if provided code is not valid)
login = rs.login(username, password, mfa)
print('Logged in!')

# set default values, wait a minute to let prices shift a little so that we can figure if price is rising or falling
action = 'buy'
last_price = float(rs.stocks.get_latest_price(target_stock)[0])
stock_amount = 0
profit = 0
bought = 0
sold = 0
transactions = 0
target_price = 0
sleep(60)

# while we are in the time range, execute code
while start_time < current_time < end_time:

    # check to make sure we still have enough money left to keep buying stuff, otherwise kill it
    # if we are selling, then we aren't worried about this
    if action == 'buy':
        account_info = rs.profiles.load_account_profile()
        buying_power = float(account_info['buying_power'])
        if buying_power < spend:
            print('Your buying power is less than your specified spend amount.  The program will now stop running.')
            print(f'Target Stock {target_stock} Daily Summary')
            print(f'Total purchase amount: ${bought}')
            print(f'Total sell amount: ${sold}')
            print(f'Resultant profit: ${profit} with {stock_amount} stocks left over.')
            exit('Your buying power is too low to continue.  Add funds or lower your spend amount before trying again.')

    # pull current price of the target stock and compare to last known price to see if it's rising/falling
    current_price = float(rs.stocks.get_latest_price(target_stock)[0])
    if current_price < last_price:
        path = 'drop'
    elif current_price > last_price:
        path = 'rise'
    else:
        path = 'hold'
    last_price = current_price

    # trigger a buy if we are trying to buy and price has turned to rise (trying to buy at the dip)
    if action == 'buy' and path == 'rise':
        action = 'sell'
        last_price = float(rs.stocks.get_latest_price(target_stock)[0])
        stock_amount = round(spend / last_price, 6)
        print(rs.orders.order_buy_fractional_by_quantity(target_stock, stock_amount, timeInForce='gfd'))
        bought = bought + spend
        print(f'bought {stock_amount} at {current_time} at {current_price}')
        target_price = last_price

    # trigger a sell if we are trying to sell, and price has turned to fall (trying to buy at the peak)
    # ensures we are selling above what we bought at for a profit
    if action == 'sell' and path == 'drop' and last_price > target_price:
        action = 'buy'
        print(rs.orders.order_sell_fractional_by_quantity(target_stock, stock_amount, timeInForce='gfd'))
        transactions = transactions + 1
        sold = sold + (stock_amount * current_price)
        print(f'sold {stock_amount} at {current_time} at {current_price}')

    # wait one minute before checking again
    sleep(60)
    current_time = datetime.now()

# summary report at the end of the day
else:
    print(f'Target Stock {target_stock} Daily Summary')
    print(f'Total purchase amount: ${bought}')
    print(f'Total sell amount: ${sold}')
    print(f'Resultant profit: ${profit} with {stock_amount} stocks left over.')
