""" Module grabs interesting data from yahoo """

import pandas
import urllib2
import re
import os

def decorate_table(table):
    """ Adds the yield, split adjustment, basis adjustment and ensemble adjusted close columns to a vanilla table """

    table["Yield"] = table['Dividends'] / table['Close']
    accumulated_yield = (table["Yield"] + 1.0).dropna().cumprod()

    #pull all splits forward in time, and fill any remaining nulls with 1
    table["Split Adjustment"] = table["SplitRatio"].fillna(method='ffill').fillna(1)

    #note: we assume dividends are reinvested on the day of
    table["Basis Adjustment"] = accumulated_yield.reindex(table.index,
                                                          method='ffill',
                                                          fill_value=1.0)
    table["Adjusted Close"] = (table["Close"] *
                               table["Basis Adjustment"] *
                               table["Split Adjustment"])
    return table

def load_symbol(symbol):
    """ Generates files we should be looking for and loads symbol from those files """

    data_directory = "data"
    price_file = "{0}/{1}.csv".format(data_directory, symbol)
    dividends_file = "{0}/{1}_div.csv".format(data_directory, symbol)
    split_file = "{0}/{1}_split.csv".format(data_directory, symbol)
    return load_symbol_from_files(price_file, dividends_file, split_file)

def load_symbol_from_files(price_file, dividend_file, split_file):
    """ Reads in a symbol from price and dividend files """

    prices = pandas.read_csv(price_file, index_col="Date", parse_dates=True)
    dividends = pandas.read_csv(dividend_file, index_col="Date", parse_dates=True)
    splits = pandas.read_csv(split_file, index_col="Date", parse_dates=True)
    return decorate_table(pandas.concat([prices, dividends, splits], axis=1).sort_index())

def load_pandas():
    """ Loads required data files. Experimental """

    symbol_finder = re.compile(
        r"^" #start at the beginning
        r"(?P<symbol_name>[^_]*)" #capture a group named symbol_name of any characters ending with _, don't capture _
        r"(_[div|split])?" #it can end with _div or _split or not.
        r"\.csv$" #it must end with .csv
    )

    symbols = set(
        symbol_finder.match(directory).group("symbol_name").upper()
        for directory
        in os.listdir("./data")
        if symbol_finder.match(directory)
    )

    return dict((key, load_symbol(key)) for key in symbols)

def webload_symbol_price(symbol, begin_date, end_date):
    """ Loads a symbol's price straight from the web """

    query_params = {
        "symbol":symbol,
        "end_day":end_date.day,
        "end_month":end_date.month - 1,
        "end_year":end_date.year,
        "begin_day":begin_date.day,
        "begin_month":begin_date.month - 1,
        "begin_year":begin_date.year
    }
    query_string = (
        "http://ichart.finance.yahoo.com/table.csv?"
        "s=%(symbol)s&"
        "d=%(end_month)d&"
        "e=%(end_day)d&"
        "f=%(end_year)d&"
        "g=d&"
        "a=%(begin_month)d&"
        "b=%(begin_day)d&"
        "c=%(begin_year)d"
        "&ignore=.csv"
    ) % query_params
    return pandas.read_csv(urllib2.urlopen(query_string), index_col="Date", parse_dates=True)
