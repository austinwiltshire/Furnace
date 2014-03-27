""" Module grabs interesting data from yahoo """

import datetime
import csv
import pandas

def make_price_line(line):
    """ Creates a data structure from a line from a yahoo csv file """
    #TODO: probably put into data frame format
    return {"Date":datetime.datetime.strptime(line[0], "%Y-%m-%d"),
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
    return {"Date":datetime.datetime.strptime(line[0], "%Y-%m-%d"),
            "Dividend":float(line[1])}

def load_dividend_csv_file(filename):
    """ Loads a csv file with dividend format """
    dividend_lines = [make_dividend_line(line) for line in load_yahoo_csv_file(filename)]
    return dict([(dividend_line["Date"], dividend_line) for dividend_line in dividend_lines])

def load_pandas():
    """ Loads required data files. Experimental """
    return {"SPY" : {"price" : pandas.read_csv("data/spy.csv", index_col="Date", parse_dates=True),
                     "dividends" : pandas.read_csv("data/spy_div.csv", index_col="Date", parse_dates=True)},
            "LQD" : {"price" : pandas.read_csv("data/lqd.csv", index_col="Date", parse_dates=True),
                     "dividends" : pandas.read_csv("data/lqd_div.csv", index_col="Date", parse_dates=True)}}
def load():
    """ Loads the yahoo spy csv file
        Note: these files need to be located in the data or root directory """
    return {"SPY" : {"price" : load_price_csv_file("data/spy.csv"),
                     "dividends" : load_dividend_csv_file("data/spy_div.csv")},
            "LQD" : {"price" : load_price_csv_file("data/lqd.csv"),
                     "dividends" : load_dividend_csv_file("data/lqd_div.csv")}}
