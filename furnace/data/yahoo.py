""" Module grabs interesting data from yahoo """

import pandas

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
