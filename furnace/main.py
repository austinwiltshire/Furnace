""" A utility file for rapid prototyping """
import furnace.performance
import furnace.data.yahoo
import furnace.data.asset
import furnace.data.fcalendar
import datetime
import furnace.strategy
import matplotlib.pyplot
#import numpy

def main():
    """ Whatever is being prototyped can be put in here """

    data_cache = furnace.data.yahoo.load_pandas()

    calendar = furnace.data.fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))
    asset_factory = furnace.data.asset.AssetUniverse(["SPY", "LQD"], data_cache, calendar)

    #NOTE: don't start earlier - dividends begin in february but our data set goes back to jan. Either get earlier
    #dividend data or start later than jan.
    #NOTE: below is a monday, the first and second of the month was a weekend
    begin = calendar.nth_trading_day_after(0, datetime.datetime(2003, 2, 3))
    end = calendar.nth_trading_day_before(0, datetime.datetime(2012, 12, 31))
    stocks_and_bonds = furnace.strategy.BuyAndHoldStocksAndBonds(asset_factory, begin)
    stocks_and_bonds_perf = furnace.performance.fire_furnace(stocks_and_bonds, begin, end)

#    stocks = strategy.BuyAndHoldStocks(asset_factory, begin)
#    stocks_perf = furnace.fire(stocks, begin, end)

    fig = matplotlib.pyplot.figure()
    stocks_and_bonds_perf.plot_index(fig.add_subplot(111), 100.0)
#    stocks_perf.plot_index(100.0)
    print stocks_and_bonds_perf.cagr()
    matplotlib.pyplot.show()
#    print stocks_perf.CAGR()

if "__main__" == __name__:
    main()
