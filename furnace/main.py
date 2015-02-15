""" A utility file for rapid prototyping """
import furnace.performance
import furnace.data.yahoo
import furnace.data.asset
import furnace.data.fcalendar
import datetime
import matplotlib.pyplot
from furnace import strategy

def test_main():
    """ Whatever is being prototyped can be put in here """


    calendar = furnace.data.fcalendar.make_fcalendar(datetime.datetime(2000, 1, 1))

    #TODO: add factory function to asset factory that automatically loads the data cache.
    #can make a singleton of it
    data_cache = furnace.data.yahoo.load_pandas()
    asset_factory = furnace.data.asset.Factory(["SPY", "LQD"], data_cache, calendar)


    #NOTE: don't start earlier - dividends begin in february but our data set goes back to jan. Either get earlier
    #dividend data or start later than jan.
    #NOTE: below is a monday, the first and second of the month was a weekend
    begin = calendar.nth_trading_day_after(0, datetime.datetime(2003, 1, 2))
    end = calendar.nth_trading_day_before(0, datetime.datetime(2012, 12, 31))
    stocks_perf = furnace.performance.fire_furnace(strategy.buy_and_hold_stocks(asset_factory,
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

    #TODO: add weak test for the pyplot
    matplotlib.pyplot.show()

if "__main__" == __name__:
    test_main()
