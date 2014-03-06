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

    def _dividends(self):
        """ List of all available dividends """
        return sorted([div for div in self._data_cache[self._symbol]["dividends"].itervalues()],
                      key=lambda d: d["Date"])

    def price(self, date):
        """ Returns the price of this asset given a date. Currently returns the closing price. """
        #TODO: use financial datetime library to elevate key errors on weekends and non trading dates
        #TODO: find better way to report error to avoid stack overflow if time is before or after what's available in the data

        try:
            return self._data_cache[self._symbol]["price"][date]["Close"]
        except KeyError:
            return self.price(date - datetime.timedelta(1))

    def _adj_price(self, date):
        """ A helper method to get yahoo's adjusted price out of the data. Useful for testing that dividend accural
            algorithms are accurate. """
        #TODO: do same check as above - throw good error on key missing
        try:
            return self._data_cache[self._symbol]["price"][date]["Adjusted Close"]
        except KeyError:
            return self._adj_price(date - datetime.timedelta(1))

    def average_yield(self):
        """ Returns the average dividend yield on a *per dividend* basis for this asset
            This is not annualized! """
        yields = [div["Dividend"] / self.price(div["Date"]) for div in self._dividends()]

        return numpy.average(yields)

    def average_dividend_period(self):
        """ Returns the average period between dividend dispersals for this asset """
        dates = [div["Date"] for div in self._dividends()]
        average_days_period = [(later - earlier).days for (earlier, later) in zip(dates[:-1], dates[1:])]
        return numpy.average(average_days_period)

    def yield_between(self, begin, end):
        """ Returns the dividend yield (raw dividends / share price at the time) between begin and end """
        assert begin <= end, "Beginning date should happen before or during end date"

        dividends_in_range = [div for div in self._dividends() if begin < div["Date"] <= end]
        yields = [div["Dividend"] / self.price(div["Date"]) for div in dividends_in_range]
        return reduce(operator.mul, [1.0 + yield_ for yield_ in yields], 1.0) - 1.0

    def _expected_daily_accrued_yield(self):
        """ Returns the expected daily, non compounded, yield of this asset """
        return self.average_yield() / self.average_dividend_period()

    def _estimate_yield_accrued(self, next_dividend, past_dividend, date):
        """ Estimates the yield accrued between dividends when one is not available """
        assert not (next_dividend and past_dividend)

        days_in = ((date - past_dividend["Date"]).days
                   if not next_dividend
                   else self.average_dividend_period() - (next_dividend["Date"] - date).days)

        if days_in > self.average_dividend_period() or days_in < 0.0:
            raise Exception("Too late or early to estimate dividends")

        return days_in * self._expected_daily_accrued_yield()

    def _calculate_yield_accrued(self, next_dividend, past_dividend, date):
        """ Calculates the portion of the dividend yield accrued on date assuming both dividends are valid """
        assert next_dividend and past_dividend

        days_between = float((next_dividend["Date"] - past_dividend["Date"]).days)
        yield_ = next_dividend["Dividend"] / self.price(date)
        days_in = float((date - past_dividend["Date"]).days)

        return days_in / days_between * yield_

    def yield_accrued(self, date):
        """ Returns the yield accrued to this asset at date.
            Accrued means the dividend is owed to us, but hasn't been dispersed yet """
        next_dividend = next((div for div in self._dividends() if date < div["Date"]), None)
        past_dividend = next((div for div in reversed(self._dividends()) if date >= div["Date"]), None)

        return (self._calculate_yield_accrued(next_dividend, past_dividend, date)
                if next_dividend and past_dividend
                else self._estimate_yield_accrued(next_dividend, past_dividend, date))

#TODO: pull yahoo stuff out into yahoo subsection of data module
#TODO: and put asset into asset subsection of data module
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

