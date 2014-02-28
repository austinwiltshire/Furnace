""" Deals with the importing, parsing and storing of data """

import datetime
import csv
import operator
import numpy

def prev(iter_):
    """ Opposite of 'next' """
    return next(reversed(iter_))

class AssetFactory:
    def __init__(self, data_cache):
        self._data_cache = data_cache

    def make_asset(self, symbol):
        """ Creates an asset based on the ticker symbol """
        return Asset(symbol, self._data_cache)

class Asset(object):
    """ Represents a tradable security, by symbol """
    def __init__(self, symbol, data_cache):
        self._symbol = symbol
        self._data_cache = data_cache

    def price(self, date):
        """ Returns the price of this asset given a date. Currently returns the closing price. """
        #TODO: use financial datetime library to elevate key errors on weekends and non trading dates

        try:
            return self._data_cache[self._symbol]["price"][date]["Close"]
        except KeyError:
#            print date
            return self.price(date - datetime.timedelta(1))

    def adj_price(self, date):
        try:
            return self._data_cache[self._symbol]["price"][date]["Adjusted Close"]
        except KeyError:
            return self.adj_price(date - datetime.timedelta(1))

    def average_yield(self):
        """ Returns the average dividend yield on a *per dividend* basis for this asset
            This is not annualized! """
        dividends = [div for div in self._data_cache[self._symbol]["dividends"].itervalues()]
        yields = [div["Dividend"] / self.price(div["Date"]) for div in dividends]
        return numpy.average(yields)

    def average_dividend_period(self):
        """ Returns the average period between dividend dispersals for this asset """
        dividends = [div for div in self._data_cache[self._symbol]["dividends"].itervalues()]
        dates = sorted([div["Date"] for div in dividends])
        average_days_period = [(later - earlier).days for (earlier, later) in zip(dates[:-1], dates[1:])]
        return numpy.average(average_days_period)

    def yield_between(self, begin, end):
        """ Returns the dividend yield (raw dividends / share price at the time) between begin and end """
        #TODO: check range boundries. do we want to count dividend as <= ... < or < ... <=?
        
        dividends = [div for div in self._data_cache[self._symbol]["dividends"].itervalues() if begin < div["Date"] <= end]
        return reduce(operator.mul, [1.0 + (div["Dividend"] / self.price(div["Date"])) for div in dividends], 1.0) - 1.0

    def yield_accrued(self, date):
        """ Returns the yield accrued to this asset at date. Accrued means the dividend is owed to us, but hasn't been dispersed yet """
        dividends = sorted([div for div in self._data_cache[self._symbol]["dividends"].itervalues()],
                           key=lambda d: d["Date"])
        try:
            next_dividend = next(div for div in dividends if date < div["Date"])
        except StopIteration:
            #next dividend not found.
            past_dividend = next(div for div in reversed(dividends) if date > div["Date"])
            days_in = (date - past_dividend["Date"]).days
            return (days_in / self.average_dividend_period()) * self.average_yield()
        try:
            past_dividend = next(div for div in reversed(dividends) if date > div["Date"])
        except StopIteration:
            #past dividend not found
            days_in = max(self.average_dividend_period() - (next_dividend["Date"] - date).days, 1)
            return (days_in / self.average_dividend_period()) * self.average_yield()

        days_between = next_dividend["Date"] - past_dividend["Date"]
        days_in = next_dividend["Date"] - date
        proportion_accrued = float(days_in.days) / float(days_between.days)
        return proportion_accrued * (next_dividend["Dividend"] / self.price(date))


    def trailing_yield(self, date):
        """ The trailing one year yield of this asset's dividends and interest payments """
        return self.trailing_dividend(date) / self.price(date)

    def trailing_dividend(self, date):
        """ Trailing one year's total raw dividend """

        dividends = sorted(self._data_cache[self._symbol]["dividends"].itervalues(), key=lambda d: d["Date"])
        one_year_ago = date - datetime.timedelta(365)
        assert min(d["Date"] for d in dividends < one_year_ago), "Must have at least one years worth of data!"
        return sum(d["Dividend"] for d in dividends if one_year_ago < d["Date"] <= date)

def make_price_line(line):
    """ Creates a data structure from a line from a yahoo csv file """
    #TODO: probably put into data frame format
    return {"Date":datetime.datetime.strptime(line[0], "%Y-%m-%d").date(),
            "Open":float(line[1]),
            "High":float(line[2]),
            "Low":float(line[3]),
            "Close":float(line[4]),
            "Volume":int(line[5]),
            "Adjusted Close":float(line[6])}

def load_yahoo_csv_file(filename):
    """ Loads a yahoo formatted CSV file and strips header """
    return [line for line in csv.reader(open(filename))][1:]

#NOTE: data_cache will be eager loaded (current design, anyway)
def load_price_csv_file(filename):
    """ Loads a yahoo csv file """
    price_lines = [make_price_line(line) for line in load_yahoo_csv_file(filename)]
    return dict([(price_line["Date"], price_line) for price_line in price_lines])

def make_dividend_line(line):
    """ Parses a dividend line from a yahoo dividend csv file """
    return {"Date":datetime.datetime.strptime(line[0], "%Y-%m-%d").date(),
            "Dividend":float(line[1])}

def load_dividend_csv_file(filename):
    """ Loads a csv file with dividend format """
    dividend_lines = [make_dividend_line(line) for line in load_yahoo_csv_file(filename)]
    return dict([(dividend_line["Date"], dividend_line) for dividend_line in dividend_lines])

def load():
    """ Loads the yahoo spy csv file """
    return {"SPY" : {"price" : load_price_csv_file("spy.csv"), "dividends" : load_dividend_csv_file("spy_div.csv")},
            "LQD" : {"price" : load_price_csv_file("lqd.csv"), "dividends" : load_dividend_csv_file("lqd_div.csv")}}

