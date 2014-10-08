"""
We're generating a data set to answer the question of what should we have held as a percent of our portfolio in stocks
and how many trading days should pass between rebalancing such that we maximize our simplied sharpe ratio for a
portfolio that only holds stocks (SPY) and corporate bonds (LQD) for a 9 year period between 2003, 1, 2 and
2012, 12, 31.

We do this by creating all possible portfolios with stock weightings betwen 0% and 100%, and trading days between
rebalancings between 1 and 252 trading days (every 5th option, such that we try 1, 6, 11... 252 trading days between
rebalancings). We also vary start dates from 2003, 1, 2 to 2004, 1, 2 but hold our portfolio length constant at 9 years.

The intended purpose of this data set is to group by percent stocks and number of trading days between rebalancings,
averaging the resultant simplied sharpe ratio metrics accross all possible start dates to eliminate any bias due to
lucky initial start times
"""

import furnace.data.yahoo
import furnace.data.asset
import furnace.data.fcalendar
import datetime
import numpy
import csv
import itertools
from IPython.parallel import Client
import furnace.performance
import furnace.strategy

def main():
    """ Set up the parallel engine and the data space. Call the parallel engine, then write out the results """

    client = Client()[:]
    client.use_dill()
    client.execute("import furnace.performance, furnace.strategy, numpy, datetime")

    stock_percents = numpy.linspace(0.0, 1.0, 31)
    rebalancing_periods = numpy.arange(1, 252, 5)
    days_in = numpy.arange(1, 250, 1)
    begin = datetime.datetime(2003, 1, 2)
    end = datetime.datetime(2011, 12, 31)
    grid = list(itertools.product(stock_percents, rebalancing_periods, days_in))
    builder = function_builder(begin, end)
    results = client.map(builder, grid)

#TODO: does pandas have a plain 'save to csv' function?
    with open('data.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['days_out', 'pct', 'ndays', 'r2r', 'cagr', 'ntrades'])
        writer.writerows(results)

#NOTE: went with a closure over an object as the object only has one method (this drew a warning in python).
#Seriously, it does make sense to just use a closure if you only need a single function - objects are for
#multiple related closures.
def function_builder(begin, end):
    """ Builds a test function that is closed over begin and end dates """
    fcalendar = furnace.data.fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))
    data_cache = furnace.data.yahoo.load_pandas()

    #TODO: should there be a higher level object that combines asset universe and financial calendar?
    asset_factory = furnace.data.asset.AssetUniverse(["SPY", "LQD"], data_cache, fcalendar)
    begin = begin
    end = end

    def func(args):
        """
        Given a stock percent, rebalancing period and days out, return the simplified sharpe ratio, cagr and number of
        trades for a portfolio following those parameters between begin and end
        Args is a tuple of stock percent between 0 and 1.0, rebalancing period as an integer, and days out
        as an integer.
        """
        stock_percent, rebalancing_period, days_out = args
        strategy_ = furnace.strategy.ndays_rebalance_multi_asset(asset_factory,
                                                                 fcalendar,
                                                                 ["SPY", "LQD"],
                                                                 [stock_percent, 1.0 - stock_percent],
                                                                 rebalancing_period)
        begin_date = fcalendar.nth_trading_day_after(numpy.int(days_out), begin)
        end_date = fcalendar.nth_trading_day_after(numpy.int(days_out), end)
        assert begin_date >= datetime.datetime(2003, 1, 2)
        assert end_date <= datetime.datetime(2012, 12, 31)

        performance_ = furnace.performance.fire_furnace(strategy_, begin_date, end_date)
        return (days_out, stock_percent, rebalancing_period, performance_.simple_sharpe(), performance_.cagr(),
                performance_.number_of_trades())

    return func

if __name__ == "__main__":
    main()
