""" A utility file for rapid prototyping """
import furnace.performance
import furnace.data.yahoo
import furnace.data.asset
import datetime
import furnace.strategy
import matplotlib.pyplot
#import numpy

def main():
    """ Whatever is being prototyped can be put in here """
    furnace_ = furnace.performance.Furnace()

    data_cache = furnace.data.yahoo.load_pandas()

    asset_factory = furnace.data.asset.AssetFactory(data_cache)
    begin = datetime.datetime(2003, 1, 2)
    end = datetime.datetime(2012, 12, 31)
    stocks_and_bonds = furnace.strategy.BuyAndHoldStocksAndBonds(asset_factory, begin)
    stocks_and_bonds_perf = furnace_.fire(stocks_and_bonds, begin, end)

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
