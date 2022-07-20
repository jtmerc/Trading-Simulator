# Import modules - Run jupyter-lab
import pandas as pd
import numpy as np
import pandas_datareader as web
import datetime as dt
import math
import yfinance as yf
import warnings

warnings.filterwarnings("ignore")

stocks = []
f = open("./symbols.txt", "r")
for line in f:
    stocks.append(line.strip())

f.close()

start = dt.datetime(2000, 1, 1)
end = dt.datetime(2022, 7, 1)

web.DataReader('GME', "yahoo", start="2000-1-1", end="2022-7-1")["Adj Close"].to_csv("prices.csv")
web.DataReader('GME', "yahoo", start="2000-1-1", end="2022-7-1")["Volume"].to_csv("volume.csv")

prices = pd.read_csv("prices.csv", index_col="Date", parse_dates=True)
volumechanges = pd.read_csv("volume.csv", index_col="Date", parse_dates=True).pct_change()*100

today = dt.date(2000, 1, 15)
simend = dt.date(2022, 7, 1)
tickers = []
transactionid = 0
money = 1000000
portfolio = {}
activelog = []
transactionlog = []


# Get current price
def getprice(date, ticker):
    global prices
    return prices.loc[date][ticker]


# Transaction function
def transaction(id, ticker, amount, price, type, info):
    global transactionid
    if type == "buy":
        exp_date = today + dt.timedelta(days=14)
        transactionid += 1
    else:
        exp_date = today
    if type == "sell":
        data = {"id": id, "ticker": ticker, "amount": amount, "price": price, "date": today,
                "type": type, "exp_date": exp_date, "info": info}
    elif type == "buy":
        data = {"id": transactionid, "ticker": ticker, "amount": amount, "price": price, "date": today,
                "type": type, "exp_date": exp_date, "info": info}
        activelog.append(data)
    transactionlog.append(data)


# Buy function
def buy(interestlst, allocated_money):
    global money, portfolio
    for item in interestlst:
        price = getprice(today, item)
        if not np.isnan(price):
            quantity = math.floor(allocated_money/price)
            money -= quantity*price
            portfolio[item] += quantity
            transaction(0, item, quantity, price, "buy", "")


# Sell function
def sell():
    global money, portfolio, prices, today
    itemstoremove = []
    for i in range(len(activelog)):
        log = activelog[i]
        if log["exp_date"] <= today and log["type"] == "buy":
            tickprice = getprice(today, log["ticker"])
            if not np.isnan(tickprice):
                money += log["amount"]*tickprice
                portfolio[log["ticker"]] -= log["amount"]
                transaction(log["id"], log["ticker"], tickprice, "sell", log["info"])
                itemstoremove.append(i)
            else:
                log["exp_date"] += dt.timedelta(days=1)
    itemstoremove.reverse()
    for elem in itemstoremove:
        activelog.remove(activelog[elem])


# Simulation
def simulation():
    global today, volumechanges, money
    start_date = today - dt.timedelta(days=14)
    series = volumechanges.loc[start_date:today].mean()
    interestlst = series[series > 100].index.tolist()
    sell()
    if len(interestlst) > 0:
        moneyToAllocate = 500000/len(interestlst)
        buy(interestlst, moneyToAllocate)


# Helper function
def getindices():
    global tickers
    f = open("symbols.txt", "r")
    for line in f:
        tickers.append(line.strip())
    f.close()


# Decides if today is a trading day
def tradingday():
    global prices, today
    return np.datetime64(today) in list(prices.index.values)


# Returns our assets / returns rounded to nearest hundredth
def currentvalue():
    global money, portfolio, today, prices
    value = money
    for ticker in tickers:
        tickprice = getprice(today, ticker)
        if not np.isnan(tickprice):
            value += portfolio[ticker]*tickprice
        return int(value*100)/100


# Simulation main
def main():
    global today
    getindices()
    for ticker in tickers:
        portfolio[ticker] = 0
    while today < simend:
        while not tradingday():
            today += dt.timedelta(days=1)
        simulation()
        currentpvalue = currentvalue()
        print(currentpvalue, today)
        today += dt.timedelta(days=7)


main()

