""" A utility file for rapid prototyping """
import performance
import data
import strategy
import datetime

def main():
    """ Whatever is being prototyped can be put in here """
    furnace = performance.Furnace()

    #NOTE: data_cache will be eager loaded (current design, anyway)
    data_cache = {}
    data_cache["SPY"] = data.load()

    asset_factory = data.AssetFactory(data_cache)
    strat = strategy.BuyAndHoldStocks(asset_factory,
                                      datetime.date(2001, 1, 2))
    performance_ = furnace.fire(strat)
    performance_.plot_index(100.0)

if "__main__" == __name__:
    main()
