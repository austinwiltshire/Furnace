import datetime
import csv

class AssetFactory:
    def __init__(self, data_cache):
        self._data_cache = data_cache

    def make_asset(self, symbol):
        return Asset(symbol, self._data_cache)

class Asset:
    """ Represents a tradable security, by symbol """
    def __init__(self, symbol, data_cache):
        self._symbol = symbol
        self._data_cache = data_cache

    def price(self, date):
        #TODO: this is a little too OO given that we're going to be dealing with big rows of things, so we may end up doing a big query at the front and then looking up things in a cache
        #TODO: do a price lookup in our data warehouse
        #TODO: handle missing dates better:

        try:
            return self._data_cache[self._symbol][date]["Close"]
        except(KeyError):
            return self.price(date - datetime.timedelta(1))

def make_line(line):
    #TODO: probably put into data frame format
    return {"Date":datetime.datetime.strptime(line[0], "%Y-%m-%d").date(), "Open":float(line[1]), "High":float(line[2]), "Low":float(line[3]), "Close":float(line[4]), "Volume":int(line[5])}

def load():
    return dict([(l["Date"], l) for l in [make_line(line) for line in [l for l in csv.reader(open("spy.csv"))][1:]]])

