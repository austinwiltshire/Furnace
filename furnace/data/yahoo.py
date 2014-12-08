""" Module grabs interesting data from yahoo """

import pandas
import urllib2

def load_symbol(price_file, dividend_file, split_file):
    """ Reads in a symbol from price and dividend files """
    prices = pandas.read_csv(price_file, index_col="Date", parse_dates=True)
    dividends = pandas.read_csv(dividend_file, index_col="Date", parse_dates=True)
    splits = pandas.read_csv(split_file, index_col="Date", parse_dates=True)
    return pandas.concat([prices, dividends, splits], axis=1).sort_index()

#NOTE: data_cache will be eager loaded (current design, anyway)
def load_pandas():
    """ Loads required data files. Experimental """

    pandas_data = {}

#TODO: 1.1 remove repeated code and introspect the data directory to find all possible symbols
    pandas_data["SPY"] = load_symbol("data/spy.csv", "data/spy_div.csv", "data/spy_split.csv")
    pandas_data["LQD"] = load_symbol("data/lqd.csv", "data/lqd_div.csv", "data/lqd_split.csv")
    pandas_data["IYR"] = load_symbol("data/iyr.csv", "data/iyr_div.csv", "data/iyr_split.csv")
    pandas_data["SHV"] = load_symbol("data/shv.csv", "data/shv_div.csv", "data/shv_split.csv")
    pandas_data["UUP"] = load_symbol("data/uup.csv", "data/uup_div.csv", "data/uup_split.csv")
    pandas_data["GSG"] = load_symbol("data/gsg.csv", "data/gsg_div.csv", "data/gsg_split.csv")


    return pandas_data

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
