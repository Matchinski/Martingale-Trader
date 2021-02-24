# Names:    Mason Matchinski and Michael Conard

# Strategy: This program uses a spinoff of the Martingale betting strategy to trade cryptocurrency on Robinhood. The Martingale
#           strategy consists of doubling down after a loss has occured in order to lower average cost. This is repeated until
#           a win occurs. The positives of this method include an exponentially increasing win payout and the ability to make up
#           for past losses. The negatives of this method include exponentially increasing capital invested and a chance of 
#           losing all of it, or in the case of cryptocurrency, having it all invested. 

# Changes:  This program makes some changes to the initial Martingale strategy along with some additions to modify it to better
#           suit cryptocurrency trading. The most important change to the main strategy is that this program does not fully 
#           "double down". It has a variable called "aggression" that will typically be set somewhere between one and two and
#           acts as a mutliplier that determines how much more to bet after each loss. The changes made to better suit 
#           cryptocurrency trading include buying on a "BestInX" strategy, percentages limiting when to buy, percentages limiting
#           when to sell, and a trailing stop loss.

# BestInX:  The BestInX strategy is a simple method used to find local minimas developed by Michael and I. The program tracks how
#           many times the price has dropped in a row with a variable called "numberDown". It watches the price drop and once the
#           downward streak is broken by an increase in price it checks how long the streak was. There is a variable called
#           "requiredDownStreak" and if that variable is not met it waits for another downward streak. If it is met it is one 
#           more requirement satisfied in order to buy.

# Buying    In order to make a purchase the current price must be less than the current average price mutliplied by a variable
#           called "requiredTobuy". It must also be at the end of a streak detected by the BestInX strategy. Once these are 
#           met it will submit a market buy with an amount the size of the last buy multiplied by the "aggression" variable.

# Selling:  Once cryptocurrency is owned the program starts to try to sell it. It tracks the maximum price reached since the
#           last sale. Using the maximum price it calculates a trailing stop loss that is based on the "trailingLossPercent"
#           variable. It will allow the price to continue to rise indefinitely but as soon as it falls from a peak by that
#           percentage it will sell as long as the price is "requiredGain" above the average buy in price. It is not allowed
#           to sell for a loss.

# Notes:    The program buys on the ask price and sells on the bid price in order to make the transaction most likely to occur.
#           The ask price is what the seller wants which will be the larger number and the bid is what the buyer wants which
#           will be the smaller number.

# Imports needed
import os
import sys
import time
import pandas as pd
import datetime as dt
import robin_stocks as rs

# Functions

# Execute a buy order on <code> with $<availableFunds>
def executeBuyOrder(code, availableFunds, wait = 20):

    try:
        now = dt.datetime.now()
        print("\n%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
        print("Attempting %s buy order using $%.2f..." % (code, availableFunds))

        data = rs.orders.order_buy_crypto_by_price(code, availableFunds, "ask_price")

        # this means the order had an error and was canceled immediately
        if 'id' not in data:
            print("%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
            print("%s buy order using $%.2f failed" % (code, availableFunds))
            print("%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
            print("Error: ", end='')
            print(data)
            return 0.0, 0.0

        # wait on the order to finish
        time.sleep(wait)
        now = dt.datetime.now()
        #amount = float(getCoinOwned(coin))

        # if order succeeded, get the actual order info
        orderInfo = rs.orders.get_crypto_order_info(data['id'])
        try:
            realPrice = float(orderInfo['average_price'])
            amountBought = float(orderInfo['cumulative_quantity'])
            #moneySpent = float(orderInfo['rounded_executed_notional'])
        except Exception as e:
            # order incomplete
            cancelCryptoOrders()
            print("%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
            print("%s buy order using $%.2f timed out" % (code, availableFunds))
            return 0.0, 0.0
            
        return realPrice, amountBought

    except Exception as e:
        cancelCryptoOrders()
        print("\n\nError during buy order on line %d:" % (sys.exc_info()[-1].tb_lineno))
        print(e)
        print("")
        return 0.0, 0.0

# Execute a sell limit order on <code> for <amount> at <limitPrice>
def executeSellLimitOrder(code, amount, limitPrice, wait = 30):

    try:
        now = dt.datetime.now()
        print("\n%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
        print("Attempting %s sell limit order of %.8f at $%.2f..." % (code, float(amount), float(limitPrice)))

        data = rs.orders.order_sell_crypto_limit(code, amount, limitPrice)

        # this means the order had an error and was canceled immediately
        if 'id' not in data:
            print("%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
            print("%s sell limit order of %.8f at $%.2f failed" % (code, amount, limitPrice))
            print("%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
            print("Error: ", end='')
            print(data)
            return 0.0, 0.0

        # wait on the order to finish
        time.sleep(wait)
        now = dt.datetime.now()

        # order succeeded, get the actual order info
        orderInfo = rs.orders.get_crypto_order_info(data['id'])
        try:
            realPrice = float(orderInfo['average_price'])
            #amountSold = float(orderInfo['cumulative_quantity'])
            moneyObtained = float(orderInfo['rounded_executed_notional'])

        except Exception as e:
            # order incomplete
            cancelCryptoOrders()
            print("%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
            print("%s sell limit order of %.8f at $%.2f timed out" % (code, amount, limitPrice))
            return 0.0, 0.0

        # logging
        return realPrice, moneyObtained

    except Exception as e:
        cancelCryptoOrders()
        print("\n\nError during sell limit order on line %d:" % (sys.exc_info()[-1].tb_lineno))
        print(e)
        print("")
        return 0.0, 0.0

# Cancel all crypto orders
def cancelCryptoOrders():
    save_stdout = sys.stdout
    sys.stdout = open(os.devnull, "w")
    rs.orders.cancel_all_crypto_orders()
    sys.stdout = save_stdout

# Logs in to Robinhood via 'login.secret' file
def loginToRobinhood():

    login = open('Login.secret', 'r')
    username = login.readline().strip()
    password = login.readline().strip()
    login.close()

    try:
        rs.login(username, password)
        print("Login succeeded\n")
    except:
        print("Login failed\n")
        exit()

# Aligns script to real time interval specified
def alignClock(period, periodType):
    """
        period: integer between 1 and 60
        periodType: 'second' or 'minute'
    """

    now = dt.datetime.now()

    if periodType == "minute":
        timeToSleep = ((period - (now.minute % period)) * 60) - now.second - (now.microsecond / 1000000)
    elif periodType == "second":
        timeToSleep = period - (now.second % period) - (now.microsecond / 1000000)
    
    time.sleep(timeToSleep)

# Gathers the latest price data
def displayCurrentPrices(code):

    ask, bid, mark = getLiveCryptoPrices(code)

    now = dt.datetime.now()
    print("%s> " % (now.strftime("%Y-%m-%d %H:%M:%S")), end='')
    print("%s price: bid = %.4f, mark = %.4f, ask = %.4f" % (code, bid, mark, ask), flush=True)

# Return the instantaneous ask, bid, and dispay price of a given ticker
def getLiveCryptoPrices(code):

    data = rs.crypto.get_crypto_quote(code)
    return float(data['ask_price']), float(data['bid_price']), float(data['mark_price'])

# Return the amount of bitcoin you currently own
def getCoinOwned(code):

    profile = rs.crypto.get_crypto_positions()
    i = 0
    while i < len(profile):
        if profile[i]['currency']['code'] == code:
            return float(profile[i]['quantity'])
        i += 1
    return 0.0

# Print stats after a sell
def printStats(maxPrice, trailPrice, bought, totalSpent, average, currentBid, personallySold, numBuys, currentProfit, scaled):
    
    print('   Number Of Buys:  {:<d}'.format(numBuys))
    print('Max Price Reached: ${:<.2f}'.format(maxPrice))
    print('    Trailing Stop: ${:<.2f}'.format(trailPrice))
    print('  Cheapest Buy In: ${:<.2f}'.format(bought))
    print('    Average Price: ${:<.2f}'.format(average))
    print('      Total Spent: ${:<.2f}'.format(totalSpent))
    print('     Full Sold At: ${:<.2f}'.format(currentBid))
    print('          Sold At: ${:<.2f}'.format(personallySold))
    print('           Profit: ${:<.2f}'.format(currentProfit))   
    print('    Scaled Profit: ${:<.2f}'.format(scaled))   
    print('_____________________________________________________________________________')

# User configured values
trailingLossPercent = 0.995       # The percentage the price needs to fall from the peak to trigger a sell 
requiredDownStreak  = 4           # The number of times in a row that the price needs to fall to satisfy the BestInX strategy
clockAlignDelay     = 30          # The time interval that the program aligns to in order to grab cryptocurrency data
requiredToBuy       = 0.94        # The percentage the price needs to fall from the current average price in order to buy
requiredGain        = 1.01        # The percentage the price needs to gain at a minimum in order to sell
aggression          = 1.25        # The amount to increase each "doubel down" by
buyAmount           = 100         # The value of the first buy in
verbose             = True        # Flag that says whether to show verbose debugging print statements or not
coin                = 'ETH'       # The cryptocurrency being traded

# Clear the terminal before each run
clear = lambda: os.system('cls')
clear()

# Login to Robinhood
loginToRobinhood()

# Buying initializations
numberDown          = 0           # The number of times in a row the price has dropped
boughtAt            = 100_000     # The price of the most recent buy in
lastAsk             = 0           # The previous price people will sell the currency at
buy                 = True        # The flag determining if the program is allowed to buy

# Selling initializations
maxPriceAfterBuy    = 0           # The highest price reached after the last sale
trailingStopLoss    = 0           # The calculated stop loss price that it will sell at if the price falls from its peak
sell                = False       # The flag determining if the program is allowed to sell

# Stat calculation initializations
totalValueInvested  = 0           # The sum of the value of all of the buy ins in USD
totalCryptoCost     = 0           # The sum of the value of all of the buy ins in the selected cryptocurrency
averageSpending     = 0           # The average size of the buy ins in USD
scaledProfit        = 0           # The profit scaled down from full coin prices to invested USD
numberOfBuys        = 0           # The number of times the program has bought in since the last sell
averageCost         = 0           # The average cost of all of the buy ins in full coins since the last sell
profit              = 0           # The amount of money made in total in full coins

# Align the program to the user selected time interval
alignClock(clockAlignDelay, 'second')

# The main loop that runs indefinitely
while True:

    # Attempt to retrieve the live data prices
    try:
        ask, bid, mark = getLiveCryptoPrices(coin) 
        
        if verbose is True:
            print('The current bid and ask prices are: ${:<.2f}, ${:<.2f}'.format(round(bid, 2), round(ask, 2)))
            
            if ask < lastAsk:
                print('Current ask is LESS: ${:<.2f}'.format(round(ask, 2)))
            elif ask == lastAsk:
                print('Current ask is SAME: ${:<.2f}'.format(round(ask, 2)))
            else:
                print('Current ask is MORE: ${:<.2f}'.format(round(ask, 2)))
            
    # If the live data cannot be retrieved print an error and continue
    except:
        print('Failed to get live data!')

    # If the bid prices reaches a new maximum since the last sell happened calculate the new trailing stop loss value
    if bid > maxPriceAfterBuy:
        maxPriceAfterBuy = bid
        trailingStopLoss = round(maxPriceAfterBuy * trailingLossPercent, 2)

        if verbose is True:
            print('Current maxPriceAfterBuy is: ${:<.2f}'.format(round(maxPriceAfterBuy, 2)))
            print('Current trailingStopLoss is: ${:<.2f}'.format(trailingStopLoss))


    # Currently heading down
    if ask < lastAsk:
        numberDown += 1
        buy = True

    # Switched to heading up (BUY)
    elif ask > lastAsk and ask < boughtAt * requiredToBuy and numberDown >= requiredDownStreak and buy is True:

        buyAmount = buyAmount * aggression ** numberOfBuys
        orderPrice, amountBought = executeBuyOrder(coin, buyAmount) 

        if amountBought != 0.0:
            boughtAt = orderPrice
            amountSpent = orderPrice * amountBought
            print('Bought at: ${:<.2f}, numCoins: {:<.8f}, spent: ${:<.2f}'.format(round(boughtAt, 2),amountBought, amountSpent))

            # Reset stop loss peak
            maxPriceAfterBuy = 0

            # Reset downward trend counter
            numberDown = 0

            # Increment the number of buys
            numberOfBuys += 1

            # Increment the total amount invested
            totalValueInvested += amountSpent
            totalCryptoCost += orderPrice

            # Calculate the new average cost
            averageSpending = round(totalValueInvested / numberOfBuys, 2)
            averageCost = round(totalCryptoCost / numberOfBuys, 2)

            # Must wait for a new buy trigger and is now able to sell
            buy = False
            sell = True

    # Downward trend was broken and counter needs reset
    if ask > lastAsk:
        numberDown = 0

    # (SELL)
    if bid < trailingStopLoss and bid > averageCost * requiredGain and sell is True:   
        
        # Get the amount of <coin> currently owned 
        amount = getCoinOwned(coin)

        orderPrice, moneyObtained = executeSellLimitOrder(coin, amount, round(bid,2))

        if moneyObtained != 0.0:
            soldAt = orderPrice
            numCoinsSold = moneyObtained / orderPrice
            personallySold = soldAt * numCoinsSold

            # Calculate the profit made with this sale
            gains = (soldAt - averageCost) * numberOfBuys

            # Adjust the profit from whole coins down to current investment size
            scaledGains = gains * (buyAmount / averageCost)
            
            # Print all of the stats after the sale
            printStats(maxPriceAfterBuy, trailingStopLoss, boughtAt, averageSpending, averageCost, soldAt, personallySold, numberOfBuys, gains, scaledGains)

            # Reset tracking variables
            averageCost = 0

            # Reset the number of buys
            numberOfBuys = 0

            # Reset the total amount invested
            totalValueInvested = 0

            # Reset initial bought at value
            boughtAt = 100_000

            # Turn off sell flag
            sell = False

    # Save last bid price and update the index
    lastAsk = ask

    # Align the program to the time
    alignClock(clockAlignDelay, 'minute')
