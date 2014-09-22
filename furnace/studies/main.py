""" A utility file for rapid prototyping """
import furnace.performance
import furnace.data.yahoo
import furnace.data.asset
import furnace.data.fcalendar
import datetime
import numpy
import csv
import itertools
from multiprocessing import Process, Queue

def strategy_builder(begin, end):
    """ Helper provides a factory method that returns strategy performance objects """
    fcalendar = furnace.data.fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))
    data_cache = furnace.data.yahoo.load_pandas()
    asset_factory = furnace.data.asset.AssetUniverse(["SPY", "LQD"], data_cache, fcalendar)

    def get_performance(stock_percent, rebalancing_period, days_out):
        """ Builds a rebalanced strategy of spy and lqd with the above parameters

        stock_percent: the percent stocks to put in the strategy, must be between 0 and 1.0
        rebalancing_period: number of days between rebalancing
        days_out: how far out from the begin date to start our window

        returns: performance metrics for the built strategy """
        strategy_ = furnace.strategy.ndays_rebalance_multi_asset(asset_factory,
                                                                 fcalendar,
                                                                 ["SPY", "LQD"],
                                                                 [stock_percent, 1.0 - stock_percent],
                                                                 rebalancing_period)
        begin_date = fcalendar.nth_trading_day_after(numpy.int(days_out), begin)
        end_date = fcalendar.nth_trading_day_after(numpy.int(days_out), end)
        assert begin_date >= datetime.datetime(2003, 1, 2)
        assert end_date <= datetime.datetime(2012, 12, 31)

        return furnace.performance.fire_furnace(strategy_, begin_date, end_date)

    return get_performance

def run_f(builder, queue, test_set):
    """ Helper method for the multiprocessing module to build this data set """
    for pct, rebalance, days_out in test_set:
        performance_ = builder(pct, rebalance, days_out)
        queue.put((pct,
                   rebalance,
                   days_out,
                   performance_.reward_risk_ratio(),
                   performance_.cagr(),
                   performance_.number_of_trades()))

def test_main():
    """
    I want to generate a grid search of the two variables:
        1. percent of a portfolio held by stocks from 0 to 100%
        2. rebalancing period for now between 1 and 252 days
    I want to generate strategies based on these variables, fire them, and collect cagr, number of trades and
    risk reward metrics.
    I want to write out the inputs - percent portfolio, rebalancing rule, and the outputs as described above
    to a csv file.
    I want to then make a 3d graph with the inputs on the x and y, and the risk reward metric on the z axis.
    With this, we can consider spiral 1 development done. Probably need to pylint everything and check test
    coverage, as well as triage todos and have a design/refactoring review of code base
    """
    stock_percents = numpy.linspace(0.0, 1.0, 31)
    rebalancing_periods = numpy.arange(1, 252, 5)
    days_in = numpy.arange(1, 250, 1)
    grid = list(itertools.product(stock_percents, rebalancing_periods, days_in))
    builder = strategy_builder(datetime.datetime(2003, 1, 2), datetime.datetime(2011, 12, 31))
    queue = Queue()

    with open('data.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['days_out', 'pct', 'ndays', 'r2r', 'cagr', 'ntrades'])
        cores = 4
        ntile = len(grid) / cores
        processes = []
        for core in range(cores):
            ntile_grid = grid[core*ntile:(core+1)*ntile]
            process = Process(target=run_f, args=(builder, queue, ntile_grid))
            processes.append(process)
            process.start()

        for done in range(len(grid)):
            writer.writerow(queue.get())
            print "% done ", 100 * (float(done) / float(len(grid)))
