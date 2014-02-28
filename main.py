""" A utility file for rapid prototyping """
import performance
import data
import strategy
import datetime

def main():
    """ Whatever is being prototyped can be put in here """
    furnace = performance.Furnace()

    data_cache = data.load()

    asset_factory = data.AssetFactory(data_cache)
    begin = datetime.date(2003, 1, 2)
    end = datetime.date(2012, 12, 31)
#    strat = strategy.BuyAndHoldStocks(asset_factory, datetime.date(2001, 1, 2))
    strat = strategy.BuyAndHoldStocksAndBonds(asset_factory,
                                      datetime.date(2003, 1, 2))
    performance_ = furnace.fire(strat, begin, end)

#    error = []
#    spy = asset_factory.make_asset("SPY")
#    for date_ in range(0, (end - begin).days, 30):
#        date__ = begin + datetime.timedelta(date_)
#        my_index = performance_.index_on(date__, 100.67)
#        real_index = spy.adj_price(date__)
#        error.append(my_index - real_index)
#        print date__, my_index, real_index, spy.price(date__), my_index - real_index
#    print sum(error)

    strat2 = strategy.BuyAndHoldStocks(asset_factory, datetime.date(2003, 1, 2))
    performance2 = furnace.fire(strat2, begin, end)
    performance_.plot_index(100.0)
    performance2.plot_index(100.0)
    print performance_.CAGR()
    print performance2.CAGR()

if "__main__" == __name__:
    main()
