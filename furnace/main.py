""" A utility file for rapid prototyping """
import furnace.performance
import furnace.data.yahoo
import furnace.data.asset
import furnace.data.fcalendar
import datetime
import matplotlib.pyplot
from furnace import strategy
import numpy
import csv
import itertools
from multiprocessing import Process, Queue

class StrategyBuilder(object):
    def __init__(self, begin, end):
        self._fcalendar = furnace.data.fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))
        self._data_cache = furnace.data.yahoo.load_pandas()
        self._asset_factory = furnace.data.asset.AssetUniverse(["SPY", "LQD"], self._data_cache, self._fcalendar)
        self._begin = begin
        self._end = end

    def run_strategy(self, stock_percent, rebalancing_period, days_out):
        strategy_ = furnace.strategy.ndays_rebalance_multi_asset(self._asset_factory,
                                                                 self._fcalendar,
                                                                 ["SPY", "LQD"],
                                                                 [stock_percent, 1.0 - stock_percent],
                                                                 rebalancing_period)
        begin_date = self._fcalendar.nth_trading_day_after(numpy.int(days_out), self._begin)
        end_date = self._fcalendar.nth_trading_day_after(numpy.int(days_out), self._end)
        assert begin_date >= datetime.datetime(2003, 1, 2)
        assert end_date <= datetime.datetime(2012, 12, 31)

#        import IPython
#        IPython.embed()

        return furnace.performance.fire_furnace(strategy_, begin_date, end_date)

def run_f(builder, queue, test_set):
    for pct, rebalance, days_out in test_set:
        performance_ = builder.run_strategy(pct, rebalance, days_out)
        queue.put((pct, rebalance, days_out, performance_.reward_risk_ratio(), performance_.cagr(), performance_.number_of_trades()))


        

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
#    grid = cartesian_product(stock_percents, rebalancing_periods)
    begin = datetime.datetime(2003, 1, 2)
    end = datetime.datetime(2011, 12, 31)
    grid = list(itertools.product(stock_percents, rebalancing_periods, days_in))
    builder = StrategyBuilder(begin, end)
    queue = Queue()

    with open('data.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['days_out', 'pct', 'ndays', 'r2r', 'cagr', 'ntrades'])
        cores = 4
        ntile = len(grid) / cores
        processes = []
        for core in range(cores):
            ntile_grid = grid[core*ntile:(core+1)*ntile]
            p = Process(target=run_f, args=(builder, queue, ntile_grid))
            processes.append(p)
            p.start()

        for done in range(len(grid)):
            pct, rebalance, days_out, r2r, cagr, num_trades = queue.get()
            writer.writerow([days_out, pct, rebalance, r2r, cagr, num_trades])
            print "% done ", 100 * (float(done) / float(len(grid)))

        



#        for pct, rebalance, begin_mod in grid:
            #performance_, begin_date, pct, rebalance = builder.run_strategy(pct, numpy.int(rebalance), begin_mod)

            #writer.writerow([begin_date,
            #                 pct,
            #                 rebalance,
            #                 performance_.reward_risk_ratio(),
            #                 performance_.cagr(),
            #                 performance_.number_of_trades()])
            #i += 1
            #print "percent done", 100 * (float(i) / float(l))
            #return

def main2():
    """ Whatever is being prototyped can be put in here """


    calendar = furnace.data.fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))
    data_cache = furnace.data.yahoo.load_pandas()
    asset_factory = furnace.data.asset.AssetUniverse(["SPY", "LQD"], data_cache, calendar)


    #NOTE: don't start earlier - dividends begin in february but our data set goes back to jan. Either get earlier
    #dividend data or start later than jan.
    #NOTE: below is a monday, the first and second of the month was a weekend
    begin = calendar.nth_trading_day_after(0, datetime.datetime(2003, 1, 2))
    end = calendar.nth_trading_day_before(0, datetime.datetime(2012, 12, 31))
    stocks_perf = furnace.performance.fire_furnace(strategy.buy_and_hold_stocks(asset_factory.restricted_to(["SPY"]),
                                                                                begin,
                                                                                end),
                                                   begin,
                                                   end)

    stocks_and_bonds = furnace.strategy.buy_and_hold_stocks_and_bonds(asset_factory, begin, end)
    stocks_and_bonds_perf = furnace.performance.fire_furnace(stocks_and_bonds, begin, end)

    stocks_and_bonds_perf.plot_index(100.0)
    stocks_perf.plot_index(100.0)
    print (stocks_and_bonds_perf.cagr() - 1.0) / stocks_and_bonds_perf.volatility()
    print (stocks_perf.cagr() - 1.0) / stocks_perf.volatility()
    matplotlib.pyplot.show()

if "__main__" == __name__:
    test_main()
