""" A utility file for rapid prototyping """
import performance
import data
import numpy
import strategy
import datetime

def main():
    """ Whatever is being prototyped can be put in here """
    furnace = performance.Furnace()

    #NOTE: data_cache will be eager loaded (current design, anyway)
    data_cache = {}
    data_cache["SPY"] = data.load()

    asset_factory = data.AssetFactory(data_cache)
    spy = asset_factory.make_asset("SPY")
    strat = strategy.BuyAndHoldStocks(asset_factory,
                                      datetime.date(2001, 1, 2))
    performance_ = furnace.fire(strat)
    assert numpy.isclose(performance_.CAGR(), 1.00839746759, 1e-11, 1e-11)

    base = spy.price(datetime.date(2001, 1, 2))
    assert numpy.isclose(performance_.index_on(datetime.date(2001, 1, 2), base), 128.81)
    assert numpy.isclose(performance_.index_on(datetime.date(2001, 2, 1), base), 137.93)
    assert numpy.isclose(performance_.index_on(datetime.date(2002, 1, 2), base), 115.53)
    assert numpy.isclose(performance_.index_on(datetime.date(2012, 12, 31), base), 142.41)

if "__main__" == __name__:
    main()
