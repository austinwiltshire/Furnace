""" Module grabs interesting data from yahoo """

import pandas
import urllib2

def load_symbol(price_file, dividend_file):
    """ Reads in a symbol from price and dividend files """
    prices = pandas.read_csv(price_file, index_col="Date", parse_dates=True)
    dividends = pandas.read_csv(dividend_file, index_col="Date", parse_dates=True)
    return pandas.concat([prices, dividends], axis=1)

#NOTE: data_cache will be eager loaded (current design, anyway)
def load_pandas():
    """ Loads required data files. Experimental """

    pandas_data = {}

    pandas_data["SPY"] = load_symbol("data/spy.csv", "data/spy_div.csv")
    pandas_data["LQD"] = load_symbol("data/lqd.csv", "data/lqd_div.csv")

    return pandas_data

def webload_symbol_price(symbol, begin_date, end_date):
    """ Loads a symbol's price straight from the web """
    query_params = {"symbol":symbol,
                    "end_day":end_date.day,
                    "end_month":end_date.month - 1,
                    "end_year":end_date.year,
                    "begin_day":begin_date.day,
                    "begin_month":begin_date.month - 1,
                    "begin_year":begin_date.year}
    query_string = ("http://ichart.finance.yahoo.com/table.csv?"
                    "s=%(symbol)s&"
                    "d=%(end_month)d&"
                    "e=%(end_day)d&"
                    "f=%(end_year)d&"
                    "g=d&"
                    "a=%(begin_month)d&"
                    "b=%(begin_day)d&"
                    "c=%(begin_year)d"
                    "&ignore=.csv") % query_params
    return pandas.read_csv(urllib2.urlopen(query_string), index_col="Date", parse_dates=True)
