""" A utility file for rapid prototyping """
import performance
from data import yahoo, asset
import datetime
import strategy

def main():
    """ Whatever is being prototyped can be put in here """
    furnace = performance.Furnace()

    data_cache = yahoo.load()
    data_cache_pandas = yahoo.load_pandas()

    asset_factory = asset.AssetFactory(data_cache, data_cache_pandas)
    begin = datetime.datetime(2003, 1, 2)
    end = datetime.datetime(2012, 12, 31)
    stocks_and_bonds = strategy.BuyAndHoldStocksAndBonds(asset_factory, begin)
    stocks_and_bonds_perf = furnace.fire(stocks_and_bonds, begin, end)

#    stocks = strategy.BuyAndHoldStocks(asset_factory, begin)
#    stocks_perf = furnace.fire(stocks, begin, end)
#    stocks_and_bonds_perf.plot_index(100.0)
#    stocks_perf.plot_index(100.0)
    print stocks_and_bonds_perf.CAGR()
#    print stocks_perf.CAGR()

if "__main__" == __name__:
    main()
