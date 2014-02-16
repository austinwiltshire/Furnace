""" Deals with the importing, parsing and storing of data """

import datetime
import csv

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
            return self._data_cache[self._symbol][date]["Close"]
        except KeyError:
            return self.price(date - datetime.timedelta(1))

def make_line(line):
    """ Creates a data structure from a line from a yahoo csv file """
    #TODO: probably put into data frame format
    return {"Date":datetime.datetime.strptime(line[0], "%Y-%m-%d").date(),
            "Open":float(line[1]),
            "High":float(line[2]),
            "Low":float(line[3]),
            "Close":float(line[4]),
            "Volume":int(line[5])}

def load():
    """ Loads the yahoo spy csv file """
    return dict([(l["Date"], l) for l in [make_line(line) for line in [l for l in csv.reader(open("spy.csv"))][1:]]])

